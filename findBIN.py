import re
import os

folder_path = './cc4/cc4/'
output_file = 'hasil_valid_luhn.txt'

# Algoritma Luhn (Tetap)
def luhn_validator(card_number):
    card_number = re.sub(r'\D', '', card_number)
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

    hasil_akhir = []
    total_found = 0
    total_valid = 0

    print("Sedang memproses...")

    # Track which cards we've already found to avoid duplicates
    found_cards = set()

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            path = os.path.join(folder_path, filename)
            
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # --- Strategy 1: Multiline Labeled Format ---
                # Example:
                # Card Holder: ...
                # Card Number: ...
                # Expiration: ...
                # CVC: ...
                # Uses stricter regex to match fields, allowing for trailing whitespace.
                block_pattern = re.compile(
                    r"Card Holder:\s*(?P<name>.*?)\s*\n"
                    r"Card Number:\s*(?P<cc>\d+)\s*\n"
                    r"Expiration:\s*(?P<exp>.*?)\s*\n"
                    r"CVC:\s*(?P<cvc>.*?)\s*(?:\n|$)",
                    re.MULTILINE
                )

                for match in block_pattern.finditer(content):
                    cc = match.group("cc").strip()
                    if luhn_validator(cc):
                        if cc not in found_cards:
                            found_cards.add(cc)
                            name = match.group("name").strip()
                            exp = match.group("exp").strip()
                            cvc = match.group("cvc").strip()
                            
                            entry = (
                                f"[VALID] Matched (Multiline)\n"
                                f"CardNumber: {cc}\n"
                                f"NameOnCard: {name}\n"
                                f"ExpirationDate: {exp}\n"
                                f"CVC: {cvc}\n"
                                f"Source: {filename}"
                            )
                            hasil_akhir.append(entry)
                            total_valid += 1
                            total_found += 1
                            # print(f"Found Valid: {cc} (Multiline)")

                # --- Strategy 2: Pipe Separated Format ---
                # Iterate line by line.
                lines = content.splitlines()
                for line in lines:
                    if '|' in line:
                        # Skip if this line is part of the decorative header/footer or instruction
                        if "DAISY CLOUD" in line or "____" in line or "Join:" in line:
                            continue

                        parts = [p.strip() for p in line.split('|')]

                        # Identify which part is the CC
                        cc_index = -1
                        valid_cc = None

                        for i, part in enumerate(parts):
                            # Clean potential CC
                            potential_cc = re.sub(r'\D', '', part)
                            # Check length and Luhn
                            if potential_cc and (13 <= len(potential_cc) <= 19) and luhn_validator(potential_cc):
                                cc_index = i
                                valid_cc = potential_cc
                                break

                        if cc_index != -1:
                            if valid_cc not in found_cards:
                                found_cards.add(valid_cc)

                                name = "Unknown"
                                exp = "Unknown"
                                cvc = "Unknown"
                                
                                # Deduce fields based on position relative to CC
                                # Common Format: Name | CC | Exp | CVC  (Index 1)
                                # Common Format: CC | Exp | CVC         (Index 0)

                                if cc_index == 1:
                                    if len(parts) > 0: name = parts[0]
                                    if len(parts) > 2: exp = parts[2]
                                    if len(parts) > 3: cvc = parts[3]
                                elif cc_index == 0:
                                    if len(parts) > 1: exp = parts[1]
                                    if len(parts) > 2: cvc = parts[2]

                                entry = (
                                    f"[VALID] Matched (Pipe)\n"
                                    f"CardNumber: {valid_cc}\n"
                                    f"NameOnCard: {name}\n"
                                    f"ExpirationDate: {exp}\n"
                                    f"CVC: {cvc}\n"
                                    f"OriginalLine: {line}\n"
                                    f"Source: {filename}"
                                )
                                hasil_akhir.append(entry)
                                total_valid += 1
                                total_found += 1
                                # print(f"Found Valid: {valid_cc} (Pipe)")

            except Exception as e:
                print(f"Error file {filename}: {e}")

    # === LOGIC WRITE (Menulis Hasil) ===
    if hasil_akhir:
        try:
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write("========================================\n")
                # Gabungkan semua hasil dengan separator baris baru
                f_out.write("\n\n========================================\n".join(hasil_akhir))
                f_out.write("\n========================================\n")
            
            print(f"\nSelesai Bos!")
            print(f"Total Ditemukan Valid: {total_valid}")
            print(f"Disimpan di: {output_file}")
        except Exception as e:
            print(f"Gagal menulis file output: {e}")
    else:
        print("Zonk. Tidak ada kartu valid ditemukan.")

if __name__ == "__main__":
    scan_file_validasi_ketat()
