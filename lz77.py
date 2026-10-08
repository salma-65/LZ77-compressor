WINDOW_SIZE = 32
LOOKAHEAD_SIZE = 16

INPUT_FILE = "file1.txt"
COMPRESSED_FILE = "file2.txt"
DECOMPRESSED_FILE = "file3.txt"


# ============================================================
# 1. Read original file
# ============================================================

def read_file(filename):
    with open(filename, "rb") as file:
        return file.read()


# ============================================================
# 2. Find the longest match
# ============================================================

def find_match(data, current):
    start = max(0, current - WINDOW_SIZE)
    max_length = min(LOOKAHEAD_SIZE, len(data) - current)

    best_position = 0
    best_length = 0

    for search in range(start, current):

        length = 0

        while (
            length < max_length
            and search + length < len(data)
            and data[search + length] == data[current + length]
        ):
            length += 1

        if length > best_length:
            best_length = length
            best_position = current - search

    return best_position, best_length


# ============================================================
# 3. Compression
# ============================================================

def compress(data):
    tags = []
    current = 0

    while current < len(data):

        position, length = find_match(data, current)

        next_index = current + length

        if next_index < len(data):
            next_symbol = data[next_index]

            tags.append(
                (position, length, next_symbol)
            )

            current = next_index + 1

        else:
            tags.append(
                (position, length, None)
            )

            current = next_index

    return tags


# ============================================================
# 4. Convert number to binary
# ============================================================

def to_binary(number, bits):
    return format(number, f"0{bits}b")


# ============================================================
# 5. Convert tags to binary
# ============================================================

def convert_to_binary(tags):

    max_position = max((tag[0] for tag in tags), default=0)
    max_length = max((tag[1] for tag in tags), default=0)

    position_bits = max(1, max_position.bit_length())
    length_bits = max(1, max_length.bit_length())

    binary_tags = []

    for position, length, symbol in tags:

        position_binary = to_binary(
            position,
            position_bits
        )

        length_binary = to_binary(
            length,
            length_bits
        )

        if symbol is None:
            symbol_binary = "00000000"
        else:
            symbol_binary = to_binary(
                symbol,
                8
            )

        binary_tag = (
            position_binary
            + length_binary
            + symbol_binary
        )

        binary_tags.append(binary_tag)

    return binary_tags, position_bits, length_bits


# ============================================================
# 6. Write compressed file
# ============================================================

def write_compressed_file(filename, tags, binary_tags):

    with open(filename, "w") as file:

        for tag, binary in zip(tags, binary_tags):

            position, length, symbol = tag

            if symbol is None:
                symbol_text = "NULL"
            else:
                symbol_text = chr(symbol)

            normal_tag = (
                f"<{position}, {length}, {symbol_text}>"
            )

            # Binary divided into its 3 fields
            position_bits = binary[:-16]
            length_bits = binary[-16:-8]
            symbol_bits = binary[-8:]

            file.write(
                f"{normal_tag:<18} "
                f"{position_bits} {length_bits} {symbol_bits}\n"
            )


# ============================================================
# 7. Decompression
# ============================================================

def decompress(tags):

    output = bytearray()

    for position, length, symbol in tags:

        if position > 0 and length > 0:

            start = len(output) - position

            # Copy ONE byte at a time
            # This supports overlapping matches
            for i in range(length):
                output.append(output[start + i])

        if symbol is not None:
            output.append(symbol)

    return bytes(output)


# ============================================================
# 8. Write decompressed file
# ============================================================

def write_decompressed_file(filename, data):

    with open(filename, "wb") as file:
        file.write(data)

#============================================================
# 10 Show statistics
#===========================================================

def show_statistics(original_data, tags, position_bits, length_bits):

    # Original size in bits
    original_size = len(original_data) * 8

    # Each tag contains:
    # Position bits + Length bits + Symbol bits
    tag_size = position_bits + length_bits + 8

    # Total compressed size
    compressed_size = len(tags) * tag_size

    print("\n========== Compression Statistics ==========")
    print(f"Original size   : {original_size} bits")
    print(f"Compressed size : {compressed_size} bits")
    print(f"Tag size        : {tag_size} bits")


# ============================================================
# 9. Main
# ============================================================

def main():

    # Read file1.txt
    data = read_file("file1.txt")

    # Compress
    tags = compress(data)

    # Convert tags to binary
    binary_tags, position_bits, length_bits = convert_to_binary(tags)

    # Write file2.txt
    write_compressed_file(
        COMPRESSED_FILE,
        tags,
        binary_tags
    )

    # Decompress
    decompressed_data = decompress(tags)

    # Write file3.txt
    write_decompressed_file(
        DECOMPRESSED_FILE,
        decompressed_data
    )

    print("Compression completed.")
    print("Decompression completed.")
    print(f"Number of tags: {len(tags)}")
    print(f"Position bits: {position_bits}")
    print(f"Length bits: {length_bits}")

    if data == decompressed_data:
        print("Verification: SUCCESS")
    else:
        print("Verification: FAILED")


# ============================================================
# Run program
# ============================================================

if __name__ == "__main__":
    main() 