import os
import shutil

# --- KONFIGURASI DEFAULT ---
FOLDER_SUMBER = "/sdcard/download/Anew"
FOLDER_TUJUAN = "/sdcard/download/cc3"
KATA_KUNCI = "creditcard"

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

    keyword_lower = KATA_KUNCI.lower()
    files_found = 0
    
    print(f"--- SCANNING DIMULAI ---")
    print(f"Target: Nama file ATAU Nama folder mengandung '{KATA_KUNCI}'")
    print("-" * 40)

    # 3. Mulai Scanning
    for root, dirs, files in os.walk(FOLDER_SUMBER):
        
        # Cek apakah FOLDER tempat kita berada sekarang mengandung keyword
        # Contoh: /sdcard/download/Anew/Data-CreditCard/ (Ini dianggap MATCH)
        folder_match = keyword_lower in root.lower()
        
        for filename in files:
            # Cek apakah NAMA FILE mengandung keyword
            file_match = keyword_lower in filename.lower()
            
            # --- LOGIKA UTAMA ---
            # Jika Folder-nya cocok, AMBIL SEMUA FILE di dalamnya.
            # ATAU
            # Jika Nama File-nya cocok, AMBIL FILE ITU.
            if folder_match or file_match:
                
                source_path = os.path.join(root, filename)
                
                # Siapkan nama unik di tujuan
                unique_name = get_unique_filename(FOLDER_TUJUAN, filename)
                dest_path = os.path.join(FOLDER_TUJUAN, unique_name)
                
                try:
                    shutil.copy2(source_path, dest_path)
                    
                    # Info status
                    if folder_match and not file_match:
                        # Ini file biasa tapi ada di dalam folder target
                        print(f"[Folder Match] {filename} -> Disalin")
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
