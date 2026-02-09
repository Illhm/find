import json
import os
import re

folder_path = '/sdcard/download/cc3/'
output_file = 'hasil_valid_luhn.txt'

# Regex patterns
CARD_NUMBER_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
PIPE_ENTRY_RE = re.compile(
    r"^\s*(?P<name>[^|]*?)\s*\|\s*(?P<number>\d{13,19})\s*\|\s*"
    r"(?P<exp>\d{1,2}\s*/\s*\d{2,4})\s*(?:\|\s*(?P<cvc>\d{3,4})\s*)?$"
)
LABEL_FIELD_RE = re.compile(
    r"^\s*(?P<label>Card Holder|Card Number|Expiration|CVC|Type|Number|Exp|Holder)\s*:\s*(?P<value>.*)\s*$",
    re.IGNORECASE,
)
KATZ_FIELD_RE = re.compile(
    r"^\s*(?P<label>name|month|year|card|cvc2)\s*:\s*(?P<value>.*)\s*$",
    re.IGNORECASE,
)
EXP_RE = re.compile(r"\b(?P<month>\d{1,2})\s*/\s*(?P<year>\d{2,4})\b")
SEPARATOR_RE = re.compile(r"^\s*=+\s*$")

# Algoritma Luhn (Tetap)
def luhn_validator(card_number):
    card_number = re.sub(r'\D', '', card_number)
    if len(card_number) < 13 or len(card_number) > 19:
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

def normalize_card_number(raw_number):
    return re.sub(r"\D", "", raw_number or "")

def extract_expiration(text):
    match = EXP_RE.search(text or "")
    if not match:
        return ""
    month = match.group("month")
    year = match.group("year")
    return f"{month}/{year}"

def build_entry(card_no, name, exp, cvc, full_line, filename):
    entry_key = (
        card_no,
        name or "Unknown",
        exp or "Unknown",
        cvc or "Unknown",
        filename,
        full_line,
    )
    entry_text = (
        f"[VALID] Matched\n"
        f"CardNumber: {card_no}\n"
        f"NameOnCard: {name or 'Unknown'}\n"
        f"ExpirationDate: {exp or 'Unknown'}\n"
        f"CVC: {cvc or 'Unknown'}\n"
        f"OriginalLine: {full_line}\n"
        f"Source: {filename}"
    )
    return entry_key, entry_text

def add_entry(results, seen, entry_key, entry_text):
    if entry_key in seen:
        return
    seen.add(entry_key)
    results.append(entry_text)

def finalize_entry(entry, results, seen, filename, original_line=""):
    card_no = normalize_card_number(entry.get("number"))
    if not card_no or not luhn_validator(card_no):
        return
    entry_key, entry_text = build_entry(
        card_no,
        entry.get("name", "Unknown"),
        entry.get("exp", "Unknown"),
        entry.get("cvc", "Unknown"),
        original_line or entry.get("line", ""),
        filename,
    )
    add_entry(results, seen, entry_key, entry_text)

def parse_pipe_lines(lines, results, seen, filename):
    for line in lines:
        match = PIPE_ENTRY_RE.match(line)
        if not match:
            continue
        card_no = match.group("number")
        if not luhn_validator(card_no):
            continue
        entry_key, entry_text = build_entry(
            card_no,
            match.group("name").strip() or "Unknown",
            match.group("exp").replace(" ", ""),
            (match.group("cvc") or "").strip() or "Unknown",
            line,
            filename,
        )
        add_entry(results, seen, entry_key, entry_text)

def parse_labeled_blocks(lines, results, seen, filename):
    label_mapping = {
        "card holder": "name",
        "card number": "number",
        "expiration": "exp",
        "cvc": "cvc",
        "number": "number",
        "exp": "exp",
        "holder": "name",
    }
    current = {}
    for line in lines:
        if SEPARATOR_RE.match(line):
            finalize_entry(current, results, seen, filename)
            current = {}
            continue
        match = LABEL_FIELD_RE.match(line)
        if not match:
            continue
        label = match.group("label").lower()
        value = match.group("value").strip()
        key = label_mapping.get(label)
        if not key:
            continue
        if label == "card holder" and current.get("number"):
            finalize_entry(current, results, seen, filename)
            current = {}
        current[key] = value
        current["line"] = line
    finalize_entry(current, results, seen, filename)

def parse_katz_blocks(lines, results, seen, filename):
    current = {}
    for line in lines:
        match = KATZ_FIELD_RE.match(line)
        if not match:
            continue
        label = match.group("label").lower()
        value = match.group("value").strip()
        if label == "name" and current.get("number"):
            finalize_entry(current, results, seen, filename)
            current = {}
        if label == "card":
            current["number"] = value
        elif label == "name":
            current["name"] = value
        elif label == "month":
            current["exp_month"] = value
        elif label == "year":
            current["exp_year"] = value
        elif label == "cvc2":
            current["cvc"] = value
        current["line"] = line
        if current.get("exp_month") and current.get("exp_year"):
            current["exp"] = f"{current['exp_month']}/{current['exp_year']}"
    finalize_entry(current, results, seen, filename)

def parse_generic_lines(lines, results, seen, filename):
    for line in lines:
        for match in CARD_NUMBER_RE.finditer(line):
            card_no = normalize_card_number(match.group())
            if not luhn_validator(card_no):
                continue
            exp = extract_expiration(line)
            cvc_match = re.search(r"\b\d{3,4}\b", line)
            cvc = cvc_match.group() if cvc_match else ""
            entry_key, entry_text = build_entry(card_no, "Unknown", exp, cvc, line, filename)
            add_entry(results, seen, entry_key, entry_text)

def parse_text_file(path, filename, results, seen):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    parse_pipe_lines(lines, results, seen, filename)
    parse_labeled_blocks(lines, results, seen, filename)
    parse_katz_blocks(lines, results, seen, filename)
    parse_generic_lines(lines, results, seen, filename)

def parse_json_file(path, filename, results, seen):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    if not isinstance(data, list):
        return
    for item in data:
        if not isinstance(item, dict):
            continue
        card_no = normalize_card_number(item.get("Number", ""))
        if not card_no or not luhn_validator(card_no):
            continue
        exp_month = str(item.get("ExpMonth", "")).strip()
        exp_year = str(item.get("ExpYear", "")).strip()
        exp = f"{exp_month}/{exp_year}" if exp_month and exp_year else ""
        entry_key, entry_text = build_entry(
            card_no,
            item.get("Name", "Unknown"),
            exp or "Unknown",
            item.get("CVC", "Unknown"),
            json.dumps(item, ensure_ascii=False),
            filename,
        )
        add_entry(results, seen, entry_key, entry_text)

def scan_file_validasi_ketat():
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} tidak ditemukan!")
        return

    hasil_akhir = []
    seen_entries = set()
    total_found = 0
    total_valid = 0

    print("Sedang memproses...")

    for filename in os.listdir(folder_path):
        if not (filename.endswith(".txt") or filename.endswith(".json")):
            continue
        path = os.path.join(folder_path, filename)
        try:
            if filename.endswith(".json"):
                parse_json_file(path, filename, hasil_akhir, seen_entries)
            else:
                parse_text_file(path, filename, hasil_akhir, seen_entries)
        except Exception as e:
            print(f"Error file {filename}: {e}")

    total_valid = len(hasil_akhir)
    total_found = total_valid

    # === LOGIC WRITE (Menulis Hasil) ===
    if hasil_akhir:
        try:
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write("========================================\n")
                # Gabungkan semua hasil dengan separator baris baru
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
