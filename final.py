# ============================================================
# 1. Read original file
# ============================================================

import os

INPUT_FILE = "file1.txt"
COMPRESSED_FILE = "file2.txt"
DECOMPRESSED_FILE = "file3.txt"


def file_exists(filename):
    return os.path.isfile(filename)


def read_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


# ============================================================
# 2. Find the longest match
# ============================================================

# DO NOT CHANGE THIS PART

def find_longest_match(data, pos, search_size, lookahead_size):
    best_offset, best_length = 0, 0 
    start = max(0, pos - search_size)

    for i in range (start, pos):
        length = overlap_match(data, i , pos, lookahead_size)

        if length > best_length :
            best_offset, best_length = pos - i, length
            if best_length == lookahead_size or pos + best_length == len(data):
                break
            
    return best_offset, best_length



def overlap_match(data, candidate, pos, lookahead_size):
    distance = pos - candidate
    limit = min(len(data) - pos, lookahead_size) # Setting a limit for the function
    length = 0

    while length < limit:
        if length >= distance:  # overlap condition
            source = candidate + (length % distance)
        else:
            source = candidate + length

        if data[source] != data[pos + length]:
            break

        length += 1

    return length



def encode(data, search_size, lookahead_size):
    tuples = []
    pos = 0

    while(pos < len(data)):
        offset, length = find_longest_match(data, pos, search_size, lookahead_size)
        next_pos = pos + length
        next_symbol = data[next_pos] if next_pos < len(data) else 0 
        tuples.append((offset, length, next_symbol))
        pos+= length + 1

    return tuples


# ============================================================
# 3. Compression
# ============================================================

def compress(data, search_size, lookahead_size):
    return encode(data, search_size, lookahead_size)


# ============================================================
# 4. Convert number to binary
# ============================================================

def to_binary(number, bits):
    return format(number, f"0{bits}b")


def from_binary(binary):
    return int(binary, 2)


def calculate_bits(search_size, lookahead_size):
    position_bits = max(1, (search_size).bit_length())
    length_bits = max(1, (lookahead_size).bit_length())

    return position_bits, length_bits


# ============================================================
# 5. Convert tags to binary
# ============================================================

def convert_to_binary(tuples, position_bits, length_bits):
    binary_tags = []

    for offset, length, next_symbol in tuples:

        # Convert offset to binary
        offset_binary = to_binary(offset, position_bits)

        # Convert length to binary
        length_binary = to_binary(length, length_bits)

        # Convert next symbol to 8-bit ASCII binary
        if next_symbol == 0:
            symbol_binary = "00000000"
        else:
            symbol_binary = to_binary(ord(next_symbol), 8)

        # LZ77 binary tag
        tag = offset_binary + length_binary + symbol_binary

        binary_tags.append(tag)

    return binary_tags


def validate_tags(tags):
    for tag in tags:
        if not tag:
            raise ValueError("Empty tag found")

        if any(bit not in "01" for bit in tag):
            raise ValueError("Invalid binary tags.")

    return True


def convert_binary_to_tuples(tags, position_bits, length_bits):
    tuples = []

    tag_size = position_bits + length_bits + 8

    for tag in tags:

        if len(tag) != tag_size:
            raise ValueError("Invalid tag size.")

        # Read offset
        offset_binary = tag[:position_bits]

        # Read length
        length_binary = tag[
            position_bits:
            position_bits + length_bits
        ]

        # Read next symbol
        symbol_binary = tag[
            position_bits + length_bits:
        ]

        offset = from_binary(offset_binary)
        length = from_binary(length_binary)

        symbol_value = from_binary(symbol_binary)

        if symbol_value == 0:
            next_symbol = 0
        else:
            next_symbol = chr(symbol_value)

        tuples.append(
            (offset, length, next_symbol)
        )

    return tuples


# ============================================================
# 6. Write compressed file
# ============================================================

def write_tags(filename, tags):
    with open(filename, "w", encoding="utf-8") as file:
        for tag in tags:
            file.write(tag + "\n")


def save_compressed_file(tags, filename):
    validate_tags(tags)
    write_tags(filename, tags)


def read_tags(filename):
    with open(filename, "r", encoding="utf-8") as file:
        tags = file.read().splitlines()

    return tags


def load_compressed_file(filename):
    tags = read_tags(filename)
    validate_tags(tags)

    return tags


# ============================================================
# 7. Decompression
# ============================================================

def decode(tuples):
    output = []

    for offset, length, next_symbol in tuples:

        # Copy the matched characters
        # This also supports overlapping matches
        if length > 0:
            start = len(output) - offset

            for i in range(length):
                output.append(output[start + i])

        # Add the next symbol
        if next_symbol != 0:
            output.append(next_symbol)

    return "".join(output)


def decompress(binary_tags, position_bits, length_bits):

    # Convert binary tags back to LZ77 tuples
    tuples = convert_binary_to_tuples(
        binary_tags,
        position_bits,
        length_bits
    )

    # Decode the tuples
    return decode(tuples)


# ============================================================
# 8. Write decompressed file
# ============================================================

# handle strings or bytes

def write_file(filename, data):
    if isinstance(data, bytes):
        with open(filename, "wb") as file:
            file.write(data)
    else:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(data)


# ============================================================
# 9. Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Read original file
    # --------------------------------------------------------

    data = read_file(INPUT_FILE)

    if not data:
        print("Error: file1.txt is empty.")
        return

    # --------------------------------------------------------
    # LZ77 settings
    # --------------------------------------------------------

    search_size = 32
    lookahead_size = 16

    # --------------------------------------------------------
    # Compression
    # --------------------------------------------------------

    tuples = compress(
        data,
        search_size,
        lookahead_size
    )

    # --------------------------------------------------------
    # Calculate binary sizes
    # --------------------------------------------------------

    position_bits, length_bits = calculate_bits(
        search_size,
        lookahead_size
    )

    # --------------------------------------------------------
    # Convert LZ77 tuples to binary tags
    # --------------------------------------------------------

    binary_tags = convert_to_binary(
        tuples,
        position_bits,
        length_bits
    )

    # --------------------------------------------------------
    # Write compressed file
    # --------------------------------------------------------

    save_compressed_file(
        binary_tags,
        COMPRESSED_FILE
    )

    # --------------------------------------------------------
    # Read compressed file
    # --------------------------------------------------------

    loaded_tags = load_compressed_file(
        COMPRESSED_FILE
    )

    # --------------------------------------------------------
    # Decompression
    # --------------------------------------------------------

    decompressed_data = decompress(
        loaded_tags,
        position_bits,
        length_bits
    )

    # --------------------------------------------------------
    # Write decompressed file
    # --------------------------------------------------------

    write_file(
        DECOMPRESSED_FILE,
        decompressed_data
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    original_size = len(data) * 8

    tag_size = position_bits + length_bits + 8

    compressed_size = len(binary_tags) * tag_size

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print("\n========== LZ77 Compression ==========")

    print(f"Original size   : {original_size} bits")
    print(f"Compressed size : {compressed_size} bits")
    print(f"Number of tags  : {len(binary_tags)}")
    print(f"Position bits   : {position_bits}")
    print(f"Length bits     : {length_bits}")
    print(f"Symbol bits     : 8")
    print(f"Tag size        : {tag_size} bits")

    print("\nCompression completed.")
    print("Decompression completed.")

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    if data == decompressed_data:
        print("Verification    : SUCCESS")
    else:
        print("Verification    : FAILED")


# ============================================================
# Run program
# ============================================================

if __name__ == "__main__":
    main()