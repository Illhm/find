import re
import os
import zipfile

# File zip yang akan dibaca
zip_path = 'cc4.zip'
output_file = 'hasil_valid_luhn.txt'

# Regex lebih umum (13-19 digit)
card_pattern = r"\b\d{13,19}\b"

# Algoritma Luhn (Updated)
def luhn_validator(card_number):
    card_number = re.sub(r'\D', '', card_number)
    # Validasi panjang kartu umum (13-19 digit)
    if not (13 <= len(card_number) <= 19):
        return False
    digits = [int(d) for d in card_number]
    checksum = 0
    for i in range(len(digits) - 1, -1, -1):
        digit = digits[i]
        is_second = (len(digits) - i) % 2 == 0
        if is_second:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0

def scan_file_validasi_ketat():
    if not os.path.exists(zip_path):
        print(f"File {zip_path} tidak ditemukan!")
        return

    hasil_akhir = []
    total_found = 0
    total_valid = 0

    print("Sedang memproses...")

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Ambil semua file dalam zip
            file_list = z.namelist()
            
            for filename in file_list:
                if filename.endswith(".txt"):
                    try:
                        # Baca konten file dari dalam zip
                        with z.open(filename) as f:
                            # Decode bytes ke string
                            content = f.read().decode('utf-8', errors='ignore')
                            lines = [line.strip() for line in content.splitlines() if line.strip()]
                            
                            for i in range(len(lines)):
                                # Cek apakah ada pola kartu di baris ini
                                match = re.search(card_pattern, lines[i])
                                
                                if match:
                                    card_no = match.group()
                                    total_found += 1

                                    # Cek Validasi Luhn
                                    if luhn_validator(card_no):

                                        # === LOGIC BARU (Parsing Horizontal) ===
                                        full_line = lines[i]
                                        parts = full_line.split('|')
                                        parts = [p.strip() for p in parts] # Hapus spasi kiri/kanan

                                        # Default value kalau data tidak lengkap
                                        name = "Unknown"
                                        exp = "Unknown"
                                        cvc = "Unknown"

                                        try:
                                            # Hapus nomor kartu dari list parts biar sisa datanya aja
                                            # Kita filter yang BUKAN nomor kartu
                                            clean_parts = [p for p in parts if card_no not in p and len(p) > 1]

                                            if len(clean_parts) >= 3:
                                                name = clean_parts[0]
                                                exp = clean_parts[1]
                                                cvc = clean_parts[2]
                                            elif len(clean_parts) == 2:
                                                exp = clean_parts[0]
                                                cvc = clean_parts[1]
                                            elif len(clean_parts) == 1:
                                                exp = clean_parts[0]

                                        except Exception:
                                            pass

                                        # Format Simpan
                                        entry = (
                                            f"[VALID] Matched\n"
                                            f"CardNumber: {card_no}\n"
                                            f"NameOnCard: {name}\n"
                                            f"ExpirationDate: {exp}\n"
                                            f"CVC: {cvc}\n"
                                            f"OriginalLine: {full_line}\n"
                                            f"Source: {filename}"
                                        )
                                        hasil_akhir.append(entry)
                                        total_valid += 1
                                        print(f"Found Valid: {card_no}")

                    except Exception as e:
                        print(f"Error processing file {filename}: {e}")
    except Exception as e:
        print(f"Error opening zip file: {e}")
        return

    # === LOGIC WRITE (Menulis Hasil) ===
    if hasil_akhir:
        try:
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write("========================================\n")
                f_out.write("\n\n========================================\n".join(hasil_akhir))
                f_out.write("\n========================================\n")
            
            print(f"\nSelesai Bos!")
            print(f"Total Ditemukan: {total_found}")
            print(f"Total Valid Luhn: {total_valid}")
            print(f"Disimpan di: {output_file}")
        except Exception as e:
            print(f"Gagal menulis file output: {e}")
    else:
        print("Zonk. Tidak ada kartu valid ditemukan.")

if __name__ == "__main__":
    scan_file_validasi_ketat()
