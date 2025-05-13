import itertools
import string
from tqdm import tqdm
from pathlib import Path

def generate_capitalization_variants(word):
    """Yield all capitalization variants of the given word."""
    for pattern in itertools.product([0, 1], repeat=len(word)):
        yield ''.join(
            ch.upper() if cap and ch.isalpha() else ch.lower()
            for ch, cap in zip(word, pattern)
        )

def parse_num_range(rng):
    """Parse 'start-end' into (start, end) ints."""
    try:
        start, end = map(int, rng.split('-', 1))
    except Exception:
        raise ValueError("Numeric range must be 'start-end'.")
    if start > end:
        raise ValueError("Start must be <= end.")
    return start, end

def base_word_mode():
    bases_input = input("Enter base words (comma-separated): ").strip()
    bases = [b.strip() for b in bases_input.split(',') if b.strip()]

    symbols_input = input(
        "Enter symbols (comma-separated) or leave blank for all punctuation: "
    ).strip()
    symbols = [s for s in symbols_input.split(',') if s] if symbols_input else list(string.punctuation)

    rng = input("Enter numeric range 'start-end' (default 0-9999999): ").strip() or "0-9999999"
    num_start, num_end = parse_num_range(rng)
    outfile = input("Enter output file (default 'passwords.txt'): ").strip() or "passwords.txt"


    numeric_count = num_end - num_start + 1
    cap_count = sum(2**len(b) for b in bases)
    total = (
        cap_count * len(symbols) * numeric_count * 2  
        + cap_count * len(symbols) * 2               
        + numeric_count * len(symbols) * 2           
    )
    print(f"\nGenerating ~{total:,} passwords in base-word mode...")

    with open(outfile, 'w', encoding='utf-8') as f:
        for base in bases:
            for var in generate_capitalization_variants(base):

                for sym in symbols:
                    for num in range(num_start, num_end + 1):
                        s_num = str(num)
                        f.write(f"{var}{sym}{s_num}\n")
                        f.write(f"{s_num}{sym}{var}\n")

                for sym in symbols:
                    f.write(f"{var}{sym}\n")
                    f.write(f"{sym}{var}\n")

                for num in range(num_start, num_end + 1):
                    s_num = str(num)
                    for sym in symbols:
                        f.write(f"{s_num}{sym}\n")
                        f.write(f"{sym}{s_num}\n")

    print(f"Done! Passwords written to: {outfile}")


def brute_force_mode():
    print("Brute-force mode: generate all combinations from full charset.")
    min_len = int(input("Enter minimum length (default 3): ").strip() or 3)
    max_len = int(input("Enter maximum length: ").strip())
    outfile = input("Enter output file (default 'passwords.txt'): ").strip() or "passwords.txt"

    charset = list(
        string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation
    )
    total = sum(len(charset) ** l for l in range(min_len, max_len + 1))
    print(f"\nGenerating ~{total:,} passwords (length {min_len}-{max_len})...")

    with open(outfile, 'w', encoding='utf-8') as f:
        for length in range(min_len, max_len + 1):
            for combo in tqdm(itertools.product(charset, repeat=length), desc=f"Length {length}"):
                f.write(''.join(combo) + '\n')
    print(f"Done! Passwords written to: {outfile}")


def main():
    print("Interactive Password List Generator")
    bases_input = input(
        "Enter base words (comma-separated) or leave blank for brute-force: "
    ).strip()
    if bases_input:
        base_word_mode()
    else:
        brute_force_mode()

if __name__ == '__main__':
    main()
