import re
import os

folder_path = './cc4/cc4/'
output_file = 'hasil_valid_luhn.txt'

# General card pattern: 13 to 19 digits
card_pattern = r"\b\d{13,19}\b"

def luhn_validator(card_number):
    card_number = re.sub(r'\D', '', card_number)
    if not 13 <= len(card_number) <= 19:
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

def parse_content(content):
    results = []

    # 1. Check for Multiline Labeled Format
    # Pattern:
    # Card Holder: ...
    # Card Number: ...
    # Expiration: ...
    # CVC: ...
    #
    # Using specific regex for this block structure.
    # Note: Using [\r\n]+ to match line breaks robustly.
    # limitation: This assumes a fixed order of fields (Holder -> Number -> Expiration -> CVC).
    # If the order varies significantly, a more flexible key-value parser would be needed.

    labeled_pattern = re.compile(
        r"Card Holder:\s*(?P<name>.*?)[\r\n]+"
        r"Card Number:\s*(?P<cc>\d{13,19})[\r\n]+"
        r"Expiration:\s*(?P<exp>.*?)[\r\n]+"
        r"CVC:\s*(?P<cvc>\d*)",
        re.IGNORECASE | re.MULTILINE
    )

    for match in labeled_pattern.finditer(content):
        cc = match.group('cc')
        if luhn_validator(cc):
            results.append({
                'cc': cc,
                'name': match.group('name').strip(),
                'exp': match.group('exp').strip(),
                'cvc': match.group('cvc').strip(),
                'source_type': 'labeled',
                'original_line': match.group(0).strip()
            })

    # 2. Check for Pipe-separated Format
    # Name | CC | Exp | CVC
    # or CC | Exp | CVC

    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Optimization: Only process lines that look like they might contain a CC number
        # and contain '|'.
        if '|' in line and re.search(r'\d{13,19}', line):
            parts = [p.strip() for p in line.split('|')]

            # Find which part is the CC number
            cc_index = -1
            cc_found = None

            for i, part in enumerate(parts):
                clean_part = re.sub(r'\D', '', part)
                if 13 <= len(clean_part) <= 19 and luhn_validator(clean_part):
                    cc_found = clean_part
                    cc_index = i
                    break

            if cc_found:
                # Check if we already found this CC via labeled parser
                if any(r['cc'] == cc_found for r in results):
                    continue

                name = "Unknown"
                exp = "Unknown"
                cvc = "Unknown"

                # Deduce fields based on CC position
                if cc_index == 1:
                    # Likely: Name | CC | Exp | CVC
                    if len(parts) > 0: name = parts[0]
                    if len(parts) > 2: exp = parts[2]
                    if len(parts) > 3: cvc = parts[3]
                elif cc_index == 0:
                    # Likely: CC | Exp | CVC
                    if len(parts) > 1: exp = parts[1]
                    if len(parts) > 2: cvc = parts[2]

                # Add to results
                results.append({
                    'cc': cc_found,
                    'name': name,
                    'exp': exp,
                    'cvc': cvc,
                    'source_type': 'pipe',
                    'original_line': line
                })

    return results

def scan_file_validasi_ketat():
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} tidak ditemukan!")
        return

    hasil_akhir = []
    total_found = 0

    print(f"Scanning files in {folder_path}...")

    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]

    for filename in files:
        path = os.path.join(folder_path, filename)

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Parse content using our unified parser
            cards = parse_content(content)
            
            for card in cards:
                total_found += 1
                entry = (
                    f"[VALID] Matched ({card['source_type']})\n"
                    f"CardNumber: {card['cc']}\n"
                    f"NameOnCard: {card['name']}\n"
                    f"ExpirationDate: {card['exp']}\n"
                    f"CVC: {card['cvc']}\n"
                    f"OriginalLine: {card.get('original_line', '')}\n"
                    f"Source: {filename}"
                )
                hasil_akhir.append(entry)
                print(f"Found Valid: {card['cc']} in {filename}")

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

    # Write results
    if hasil_akhir:
        try:
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write("========================================\n")
                f_out.write("\n\n========================================\n".join(hasil_akhir))
                f_out.write("\n========================================\n")
            
            print(f"\nSelesai Bos!")
            print(f"Total Valid Cards Found: {total_found}")
            print(f"Disimpan di: {output_file}")
        except Exception as e:
            print(f"Gagal menulis file output: {e}")
    else:
        print("Zonk. Tidak ada kartu valid ditemukan.")

if __name__ == "__main__":
    scan_file_validasi_ketat()
