import os
import re
import shutil

# --- KONFIGURASI DEFAULT ---
FOLDER_SUMBER = "/sdcard/download/Anew"
FOLDER_TUJUAN = "/sdcard/download/cc3"
KATA_KUNCI = "creditcard"
SCAN_CONTENTS = True
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

FILENAME_PATTERNS = [
    re.compile(r"(?i)\bcredit\s*card\b"),
    re.compile(r"(?i)\bcc\b"),
    re.compile(r"(?i)\bcard(?:ing|s|_data)?\b"),
    re.compile(r"(?i)\bfullz?\b"),
    re.compile(r"(?i)\bcvv\b"),
]

CARD_NUMBER_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)")
EXPIRY_PATTERN = re.compile(
    r"\b(0[1-9]|1[0-2])\s*[\/\-]\s*(\d{2}|\d{4})\b|\b(20\d{2})\s*[\/\-]\s*(0[1-9]|1[0-2])\b"
)
CVV_PATTERN = re.compile(
    r"(?i)\b(cvv|cvc|cvn|cid|security\s*code)\s*[:\-]?\s*(\d{3,4})\b"
)

def get_unique_filename(destination_folder, filename):
    """
    Mencegah file tabrakan dengan rename otomatis (file_1.txt, file_2.txt)
    """
    base_name, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(destination_folder, new_filename)):
        new_filename = f"{base_name}_{counter}{extension}"
        counter += 1
    
    return new_filename

def filename_matches(name, keyword):
    keyword_lower = keyword.lower()
    if keyword_lower in name.lower():
        return True
    return any(pattern.search(name) for pattern in FILENAME_PATTERNS)

def luhn_check(number):
    total = 0
    reverse_digits = number[::-1]
    for idx, digit in enumerate(reverse_digits):
        n = int(digit)
        if idx % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

def content_has_sensitive_data(file_path):
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
            return False
        with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
            content = handle.read()
    except (OSError, UnicodeError):
        return False

    if "\x00" in content:
        return False

    for candidate in CARD_NUMBER_PATTERN.findall(content):
        digits = re.sub(r"\D", "", candidate)
        if 13 <= len(digits) <= 19 and luhn_check(digits):
            return True

    if EXPIRY_PATTERN.search(content):
        return True

    if CVV_PATTERN.search(content):
        return True

    return False

def run_search_engine():
    # 1. Cek Folder Sumber
    if not os.path.exists(FOLDER_SUMBER):
        print(f"[ERROR] Folder sumber tidak ditemukan: {FOLDER_SUMBER}")
        return

    # 2. Buat Folder Tujuan
    if not os.path.exists(FOLDER_TUJUAN):
        try:
            os.makedirs(FOLDER_TUJUAN)
        except PermissionError:
            print("[ERROR] Butuh izin storage. Ketik 'termux-setup-storage'")
            return

    files_found = 0
    
    print(f"--- SCANNING DIMULAI ---")
    print(f"Target: Nama file ATAU Nama folder mengandung '{KATA_KUNCI}'")
    if SCAN_CONTENTS:
        print("Target tambahan: Isi file mengandung data sensitif (CC/exp/cvv)")
    print("-" * 40)

    # 3. Mulai Scanning
    for root, dirs, files in os.walk(FOLDER_SUMBER):
        
        # Cek apakah FOLDER tempat kita berada sekarang mengandung keyword
        # Contoh: /sdcard/download/Anew/Data-CreditCard/ (Ini dianggap MATCH)
        folder_match = filename_matches(root, KATA_KUNCI)
        
        for filename in files:
            # Cek apakah NAMA FILE mengandung keyword
            file_match = filename_matches(filename, KATA_KUNCI)
            source_path = os.path.join(root, filename)
            content_match = False
            if SCAN_CONTENTS and not (folder_match or file_match):
                content_match = content_has_sensitive_data(source_path)
            
            # --- LOGIKA UTAMA ---
            # Jika Folder-nya cocok, AMBIL SEMUA FILE di dalamnya.
            # ATAU
            # Jika Nama File-nya cocok, AMBIL FILE ITU.
            # ATAU
            # Jika isi file mengandung data sensitif.
            if folder_match or file_match or content_match:
                
                # Siapkan nama unik di tujuan
                unique_name = get_unique_filename(FOLDER_TUJUAN, filename)
                dest_path = os.path.join(FOLDER_TUJUAN, unique_name)
                
                try:
                    shutil.copy2(source_path, dest_path)
                    
                    # Info status
                    if folder_match and not file_match:
                        # Ini file biasa tapi ada di dalam folder target
                        print(f"[Folder Match] {filename} -> Disalin")
                    elif content_match:
                        print(f"[Content Match] {filename} -> Disalin")
                    else:
                        # Ini file yang memang namanya target
                        print(f"[File Match]   {filename} -> Disalin")
                        
                    files_found += 1
                    
                except Exception as e:
                    print(f"[Gagal] {filename}: {e}")

    print("-" * 40)
    print(f"SELESAI. Total {files_found} file berhasil diamankan.")
    print(f"Lokasi: {FOLDER_TUJUAN}")

if __name__ == "__main__":
    run_search_engine()
