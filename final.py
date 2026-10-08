# ============================================================
# File Handling Functions
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

# handle strings or bytes
def write_file(filename, data):
    if isinstance(data, bytes):
        with open(filename, "wb") as file:
            file.write(data)
    else:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(data)

def write_tags(filename, tags):
    with open(filename, "w", encoding="utf-8") as file:
        for tag in tags:
            file.write(tag + "\n")

def read_tags(filename):
    with open(filename, "r", encoding="utf-8") as file:
        tags = file.read().splitlines()
    return tags

def validate_tags(tags):
    for tag in tags:
        if not tag:
            raise ValueError("Empty tag found")
        if any(bit not in "01" for bit in tag):
            raise ValueError("Invalid binary tags.")
    return True

def save_compressed_file(tags, filename):
    validate_tags(tags)
    write_tags(filename, tags)

def load_compressed_file(filename):
    tags = read_tags(filename)
    validate_tags(tags)
    return tags

def compress_file(compress_function, input_filename, output_filename):
    data = read_file(input_filename)

    tags = compress_function(data)

    save_compressed_file(tags, output_filename)


def decompress_file(decompress_function, input_filename, output_filename):
    tags = load_compressed_file(input_filename)

    data = decompress_function(tags)

    write_file(output_filename, data)


# lossless compression checker
def compare_files(first_filename, second_filename):
    with open(first_filename, "rb") as first:
        first_data = first.read()

    with open(second_filename, "rb") as second:
        second_data = second.read()

    return first_data == second_data


# ============================================================
# 1. LZ77 Settings
# ============================================================

WINDOW_SIZE = 32
LOOKAHEAD_SIZE = 16


# ============================================================
# 2. Find the longest match
# ============================================================

def find_longest_match(data, pos, search_size, lookahead_size):

    best_offset = 0
    best_length = 0

    start = max(0, pos - search_size)

    max_length = min(
        lookahead_size,
        len(data) - pos
    )

    for i in range(start, pos):

        length = 0

        while (
            length < max_length
            and i + length < len(data)
            and data[i + length] == data[pos + length]
        ):
            length += 1

        if length > best_length:

            best_offset = pos - i
            best_length = length

    return best_offset, best_length


# ============================================================
# 3. Compression
# ============================================================

def encode(data, search_size, lookahead_size):

    tuples = []

    pos = 0

    while pos < len(data):

        offset, length = find_longest_match(
            data,
            pos,
            search_size,
            lookahead_size
        )

        next_pos = pos + length

        if next_pos < len(data):

            next_symbol = data[next_pos]

            tuples.append(
                (offset, length, next_symbol)
            )

            pos = next_pos + 1

        else:

            tuples.append(
                (offset, length, None)
            )

            pos = next_pos

    return tuples


def compress(data):

    return encode(
        data,
        WINDOW_SIZE,
        LOOKAHEAD_SIZE
    )


# ============================================================
# 4. Convert number to binary
# ============================================================

def to_binary(number, bits):

    return format(
        number,
        f"0{bits}b"
    )


def from_binary(binary):

    return int(binary, 2)


# ============================================================
# 5. Convert tags to binary
# ============================================================

def convert_to_binary(tuples):

    # Find maximum offset and maximum length
    max_offset = max(
        (tag[0] for tag in tuples),
        default=0
    )

    max_length = max(
        (tag[1] for tag in tuples),
        default=0
    )

    # Calculate required number of bits
    position_bits = max(
        1,
        max_offset.bit_length()
    )

    length_bits = max(
        1,
        max_length.bit_length()
    )

    binary_tags = []

    for offset, length, next_symbol in tuples:

        # Convert offset to binary
        offset_binary = to_binary(
            offset,
            position_bits
        )

        # Convert length to binary
        length_binary = to_binary(
            length,
            length_bits
        )

        # Convert symbol to 8-bit binary
        if next_symbol is None:

            symbol_binary = "00000000"

        else:

            symbol_binary = to_binary(
                ord(next_symbol),
                8
            )

        # Combine the three fields
        binary_tag = (
            offset_binary
            + length_binary
            + symbol_binary
        )

        binary_tags.append(binary_tag)

    return (
        binary_tags,
        position_bits,
        length_bits
    )


# ============================================================
# 6. Validate binary tags
# ============================================================

def validate_binary_tags(tags):

    for tag in tags:

        if not tag:
            raise ValueError("Empty tag found")

        if any(bit not in "01" for bit in tag):
            raise ValueError(
                "Invalid binary tags."
            )

    return True


# ============================================================
# 7. Write compressed file
# ============================================================

def write_compressed_file(
    filename,
    tuples,
    binary_tags,
    position_bits,
    length_bits
):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        for tag, binary in zip(
            tuples,
            binary_tags
        ):

            offset, length, next_symbol = tag

            # Convert symbol to readable form
            if next_symbol is None:

                symbol_text = "NULL"

            else:

                symbol_text = next_symbol

            # Normal LZ77 tag
            normal_tag = (
                f"<{offset}, {length}, {symbol_text}>"
            )

            # Split binary tag into:
            # Position + Length + Symbol

            position_binary = binary[
                :position_bits
            ]

            length_binary = binary[
                position_bits:
                position_bits + length_bits
            ]

            symbol_binary = binary[
                position_bits + length_bits:
            ]

            # Write normal tag + binary representation
            file.write(
                f"{normal_tag:<18} "
                f"{position_binary} "
                f"{length_binary} "
                f"{symbol_binary}\n"
            )


# ============================================================
# 8. Read binary tags from compressed file
# ============================================================

def read_binary_tags(
    filename,
    position_bits,
    length_bits
):

    tags = []

    tag_size = (
        position_bits
        + length_bits
        + 8
    )

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            # Example:
            # <1, 2, a>       00001 00010 01100001

            parts = line.split()

            if len(parts) < 4:
                raise ValueError(
                    "Invalid compressed file format."
                )

            position_binary = parts[-3]
            length_binary = parts[-2]
            symbol_binary = parts[-1]

            binary_tag = (
                position_binary
                + length_binary
                + symbol_binary
            )

            if len(binary_tag) != tag_size:
                raise ValueError(
                    "Invalid binary tag size."
                )

            tags.append(binary_tag)

    validate_binary_tags(tags)

    return tags


# ============================================================
# 9. Convert binary tags back to tuples
# ============================================================

def convert_binary_to_tuples(
    binary_tags,
    position_bits,
    length_bits
):

    tuples = []

    tag_size = (
        position_bits
        + length_bits
        + 8
    )

    for tag in binary_tags:

        if len(tag) != tag_size:
            raise ValueError(
                "Invalid tag size."
            )

        # Read offset
        offset_binary = tag[
            :position_bits
        ]

        # Read length
        length_binary = tag[
            position_bits:
            position_bits + length_bits
        ]

        # Read symbol
        symbol_binary = tag[
            position_bits + length_bits:
        ]

        offset = from_binary(
            offset_binary
        )

        length = from_binary(
            length_binary
        )

        symbol_value = from_binary(
            symbol_binary
        )

        if symbol_value == 0:

            next_symbol = None

        else:

            next_symbol = chr(
                symbol_value
            )

        tuples.append(
            (
                offset,
                length,
                next_symbol
            )
        )

    return tuples


# ============================================================
# 10. Decompression
# ============================================================

def decode(tuples):

    output = []

    for offset, length, next_symbol in tuples:

        # Copy matched characters
        if offset > 0 and length > 0:

            start = len(output) - offset

            # Copy ONE character at a time.
            # This supports overlapping matches.

            for i in range(length):

                output.append(
                    output[start + i]
                )

        # Add next symbol
        if next_symbol is not None:

            output.append(
                next_symbol
            )

    return "".join(output)


def decompress(
    binary_tags,
    position_bits,
    length_bits
):

    # Convert binary tags
    # back to normal LZ77 tuples

    tuples = convert_binary_to_tuples(
        binary_tags,
        position_bits,
        length_bits
    )

    # Decode tuples
    return decode(tuples)


# ============================================================
# 11. Write decompressed file
# ============================================================

def write_decompressed_file(
    filename,
    data
):

    write_file(
        filename,
        data
    )


# ============================================================
# 12. Show statistics
# ============================================================

def show_statistics(
    original_data,
    tuples,
    position_bits,
    length_bits
):

    # Original size in bits
    original_size = len(
        original_data
    ) * 8

    # Each tag contains:
    # Position + Length + Symbol

    tag_size = (
        position_bits
        + length_bits
        + 8
    )

    # Total compressed size
    compressed_size = (
        len(tuples)
        * tag_size
    )

    print(
        "\n========== Compression Statistics =========="
    )

    print(
        f"Original size   : {original_size} bits"
    )

    print(
        f"Compressed size : {compressed_size} bits"
    )

    print(
        f"Tag size        : {tag_size} bits"
    )


# ============================================================
# 13. Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Check input file
    # --------------------------------------------------------

    if not file_exists(INPUT_FILE):

        print(
            f"Error: {INPUT_FILE} was not found."
        )

        return

    # --------------------------------------------------------
    # Read file1.txt
    # --------------------------------------------------------

    data = read_file(
        INPUT_FILE
    )

    if not data:

        print(
            f"Error: {INPUT_FILE} is empty."
        )

        return

    # --------------------------------------------------------
    # Compression
    # --------------------------------------------------------

    tuples = compress(
        data
    )

    # --------------------------------------------------------
    # Convert tags to binary
    # --------------------------------------------------------

    (
        binary_tags,
        position_bits,
        length_bits
    ) = convert_to_binary(
        tuples
    )

    # --------------------------------------------------------
    # Write file2.txt
    # --------------------------------------------------------

    write_compressed_file(
        COMPRESSED_FILE,
        tuples,
        binary_tags,
        position_bits,
        length_bits
    )

    # --------------------------------------------------------
    # Read binary tags from file2.txt
    # --------------------------------------------------------

    loaded_binary_tags = read_binary_tags(
        COMPRESSED_FILE,
        position_bits,
        length_bits
    )

    # --------------------------------------------------------
    # Decompression
    # --------------------------------------------------------

    decompressed_data = decompress(
        loaded_binary_tags,
        position_bits,
        length_bits
    )

    # --------------------------------------------------------
    # Write file3.txt
    # --------------------------------------------------------

    write_decompressed_file(
        DECOMPRESSED_FILE,
        decompressed_data
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    show_statistics(
        data,
        tuples,
        position_bits,
        length_bits
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print(
        "Compression completed."
    )

    print(
        "Decompression completed."
    )

    print(
        f"Number of tags: {len(tuples)}"
    )

    print(
        f"Position bits: {position_bits}"
    )

    print(
        f"Length bits: {length_bits}"
    )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    if data == decompressed_data:

        print(
            "Verification: SUCCESS"
        )

    else:

        print(
            "Verification: FAILED"
        )


# ============================================================
# Run program
# ============================================================

if __name__ == "__main__":
    main()