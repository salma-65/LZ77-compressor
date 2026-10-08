# ============================================================
# LZ77 Data Compression  (single file, with menu)
#   1. Compression      file1.txt -> file2.txt  (tags as 0/1)
#   2. Decompression    file2.txt -> file3.txt
#   3. Binary tags
#   4. Overlapping matches
#   5. Handles repetitive sequences  (e.g. <1,10,"A"> for BBBBBBBBBB)
# ============================================================

WINDOW_SIZE = 32        # search window  (max position)
LOOKAHEAD_SIZE = 16     # look-ahead     (max match length)

INPUT_FILE = "file1.txt"
COMPRESSED_FILE = "file2.txt"
DECOMPRESSED_FILE = "file3.txt"

SYMBOL_BITS = 8


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def int_to_binary(number, bits):
    """int_to_binary(5, 4) -> '0101'"""
    return format(number, f"0{bits}b")


def binary_to_int(binary):
    return int(binary, 2)


# ------------------------------------------------------------
# Find longest match  (supports OVERLAPPING matches)
# ------------------------------------------------------------
def find_longest_match(data, current):
    """
    Returns (position, length).
    position = how many steps to go back from `current` (0 = no match).
    The match is allowed to run past `current` (overlap), because we
    compare data[search + k] with data[current + k] without stopping at `current`.
    On a tie the NEAREST match wins (smallest position), like the slides.
    """
    start = max(0, current - WINDOW_SIZE)
    limit = min(LOOKAHEAD_SIZE, len(data) - current)

    best_position, best_length = 0, 0

    for search in range(start, current):          # oldest -> nearest
        length = 0
        while length < limit and data[search + length] == data[current + length]:
            length += 1

        if length > 0 and length >= best_length:  # >= : nearest wins on ties
            best_length = length
            best_position = current - search

    return best_position, best_length


# ------------------------------------------------------------
# Compression
# ------------------------------------------------------------
def compress_data(data):
    """
    bytes -> list of tags (position, length, next_symbol)
    next_symbol is None (NULL) only if the match reaches the end of the data.
    """
    tags = []
    current = 0

    while current < len(data):
        position, length = find_longest_match(data, current)
        next_index = current + length

        if next_index < len(data):
            tags.append((position, length, data[next_index]))
            current = next_index + 1
        else:
            tags.append((position, length, None))   # NULL
            current = next_index

    return tags


def tags_to_binary(tags):
    """
    Returns (header, [binary tag strings], position_bits, length_bits).

    Field widths are taken from the MAX values really used
    (same as the slides: Max Position, Max Length, 8 bits symbol).
    Tag    = [position][length][symbol 8 bits]
    Header = [position_bits: 8][length_bits: 8][last_tag_has_symbol: 1]
    """
    max_position = max((t[0] for t in tags), default=0)
    max_length = max((t[1] for t in tags), default=0)

    position_bits = max(1, max_position.bit_length())
    length_bits = max(1, max_length.bit_length())

    last_has_symbol = "0" if (tags and tags[-1][2] is None) else "1"

    header = (int_to_binary(position_bits, 8)
              + int_to_binary(length_bits, 8)
              + last_has_symbol)

    binary_tags = []
    for position, length, symbol in tags:
        symbol_value = 0 if symbol is None else symbol
        binary_tags.append(
            int_to_binary(position, position_bits)
            + int_to_binary(length, length_bits)
            + int_to_binary(symbol_value, SYMBOL_BITS)
        )

    return header, binary_tags, position_bits, length_bits


def compress_file(input_filename, output_filename):
    with open(input_filename, "rb") as f:         # bytes: no newline conversion
        data = f.read()

    tags = compress_data(data)
    header, binary_tags, pos_bits, len_bits = tags_to_binary(tags)

    # file2.txt contains ONLY 0 and 1 (header line, then one tag per line)
    with open(output_filename, "w", encoding="ascii") as f:
        f.write(header + "\n")
        for tag in binary_tags:
            f.write(tag + "\n")

    # ---- statistics (same idea as the slides) ----
    tag_size = pos_bits + len_bits + SYMBOL_BITS
    original_size = len(data) * 8
    tags_size = len(tags) * tag_size
    total_size = tags_size + len(header)

    print(f"Number of tags    : {len(tags)}")
    print(f"Tag size          : {pos_bits} + {len_bits} + {SYMBOL_BITS} = {tag_size} bits")
    print(f"Original size     : {original_size} bits")
    print(f"Compressed size   : {tags_size} bits  (tags only)")
    print(f"                    {total_size} bits  (with {len(header)}-bit header)")
    if tags_size:
        print(f"Compression ratio : {original_size / tags_size:.3f}  (tags only)")
    return tags


# ------------------------------------------------------------
# Decompression
# ------------------------------------------------------------
def read_compressed_file(filename):
    with open(filename, "r", encoding="ascii") as f:
        bits = "".join(f.read().split())          # ignore newlines / spaces

    if not bits or set(bits) - {"0", "1"}:
        raise ValueError("Invalid compressed file (must contain only 0 and 1).")

    position_bits = binary_to_int(bits[0:8])
    length_bits = binary_to_int(bits[8:16])
    last_has_symbol = bits[16] == "1"
    body = bits[17:]

    tag_size = position_bits + length_bits + SYMBOL_BITS
    tags = []
    for i in range(0, len(body) - tag_size + 1, tag_size):
        tag = body[i:i + tag_size]
        position = binary_to_int(tag[:position_bits])
        length = binary_to_int(tag[position_bits:position_bits + length_bits])
        symbol = binary_to_int(tag[position_bits + length_bits:])
        tags.append((position, length, symbol))

    return tags, last_has_symbol


def decompress_tags(tags, last_has_symbol=True):
    """
    Copies ONE BYTE AT A TIME, so a match may read bytes that were
    just appended (overlap).  e.g. <1,10,"A"> repeats the last byte 10 times.
    """
    output = bytearray()

    for index, (position, length, symbol) in enumerate(tags):
        if position > 0 and length > 0:
            start = len(output) - position
            for i in range(length):
                output.append(output[start + i])

        is_last = index == len(tags) - 1
        if not (is_last and not last_has_symbol):   # NULL symbol -> nothing to add
            output.append(symbol)

    return bytes(output)


def decompress_file(compressed_filename, output_filename):
    tags, last_has_symbol = read_compressed_file(compressed_filename)
    data = decompress_tags(tags, last_has_symbol)
    with open(output_filename, "wb") as f:
        f.write(data)
    print(f"Number of tags    : {len(tags)}")
    print(f"Decompressed size : {len(data)} bytes")


def verify_files(original_filename, decompressed_filename):
    with open(original_filename, "rb") as a, open(decompressed_filename, "rb") as b:
        return a.read() == b.read()


# ------------------------------------------------------------
# Menu
# ------------------------------------------------------------
def ask_sizes():
    global WINDOW_SIZE, LOOKAHEAD_SIZE
    w = input(f"Search window size [{WINDOW_SIZE}]: ").strip()
    l = input(f"Look-ahead size   [{LOOKAHEAD_SIZE}]: ").strip()
    if w:
        WINDOW_SIZE = max(1, int(w))
    if l:
        LOOKAHEAD_SIZE = max(1, int(l))


def menu():
    while True:
        print("\n" + "=" * 50)
        print("             LZ77 DATA COMPRESSION")
        print("=" * 50)
        print("1. Compress   (file1.txt -> file2.txt)")
        print("2. Decompress (file2.txt -> file3.txt)")
        print("3. Compress then Decompress")
        print("4. Exit")

        choice = input("\nEnter your choice: ").strip()

        try:
            if choice == "1":
                ask_sizes()
                compress_file(INPUT_FILE, COMPRESSED_FILE)
                print(f"\nCompression completed -> {COMPRESSED_FILE}")

            elif choice == "2":
                decompress_file(COMPRESSED_FILE, DECOMPRESSED_FILE)
                print(f"\nDecompression completed -> {DECOMPRESSED_FILE}")
                print("Verification:",
                      "SUCCESS (identical to file1.txt)"
                      if verify_files(INPUT_FILE, DECOMPRESSED_FILE) else "FAILED")

            elif choice == "3":
                ask_sizes()
                compress_file(INPUT_FILE, COMPRESSED_FILE)
                print()
                decompress_file(COMPRESSED_FILE, DECOMPRESSED_FILE)
                print("\nVerification:",
                      "SUCCESS (Original == Decompressed)"
                      if verify_files(INPUT_FILE, DECOMPRESSED_FILE) else "FAILED")

            elif choice == "4":
                print("\nGoodbye!")
                break

            else:
                print("\nInvalid choice. Please choose 1-4.")

        except FileNotFoundError as e:
            print("\nFile not found:", e.filename)
        except Exception as e:
            print("\nOperation failed. Error:", e)


if __name__ == "__main__":
    menu()