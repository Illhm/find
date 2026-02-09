import re
import os

folder_path = '/sdcard/download/cc3/'
output_file_all = 'all.txt'
output_file_5217 = 'find_5217.txt'

# Regex lebih umum (13-19 digit)
card_pattern = r"\b\d{13,19}\b"

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
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} tidak ditemukan!")
        return

    hasil_all = []
    hasil_5217 = []
    total_found = 0
    total_valid = 0

    print("Sedang memproses...")

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            path = os.path.join(folder_path, filename)
            
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]

                    for i in range(len(lines)):
                        # Cek apakah ada pola kartu di baris ini
                        match = re.search(card_pattern, lines[i])

                        if match:
                            card_no = match.group()
                            total_found += 1
                            
                            # Cek Validasi Luhn
                            if luhn_validator(card_no):
                                
                                # === LOGIC PARSING (Horizontal) ===
                                full_line = lines[i]
                                parts = full_line.split('|')
                                parts = [p.strip() for p in parts]

                                # Default value
                                name = "Unknown"
                                exp = "Unknown"
                                cvc = "Unknown"

                                try:
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

                                # Simpan ke list ALL
                                hasil_all.append(entry)

                                # Cek awalan 5217
                                if card_no.startswith('5217'):
                                    hasil_5217.append(entry)

                                total_valid += 1
                                print(f"Found Valid: {card_no}")

            except Exception as e:
                print(f"Error file {filename}: {e}")

    # === WRITE ALL ===
    if hasil_all:
        try:
            with open(output_file_all, 'w', encoding='utf-8') as f_out:
                f_out.write("========================================\n")
                f_out.write("\n\n========================================\n".join(hasil_all))
                f_out.write("\n========================================\n")
            print(f"Semua valid disimpan di: {output_file_all}")
        except Exception as e:
            print(f"Gagal menulis {output_file_all}: {e}")
    else:
        print("Tidak ada kartu valid ditemukan.")

    # === WRITE 5217 ===
    if hasil_5217:
        try:
            with open(output_file_5217, 'w', encoding='utf-8') as f_out:
                f_out.write("========================================\n")
                f_out.write("\n\n========================================\n".join(hasil_5217))
                f_out.write("\n========================================\n")
            print(f"Kartu 5217 disimpan di: {output_file_5217}")
        except Exception as e:
            print(f"Gagal menulis {output_file_5217}: {e}")
    else:
        print("Tidak ada kartu awalan 5217 ditemukan.")

    print(f"\nSelesai Bos!")
    print(f"Total Ditemukan (Regex): {total_found}")
    print(f"Total Valid Luhn: {total_valid}")
    print(f"Total Valid 5217: {len(hasil_5217)}")

if __name__ == "__main__":
    scan_file_validasi_ketat()
