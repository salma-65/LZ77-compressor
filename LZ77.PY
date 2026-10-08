# ============================================================
# LZ77 Data Compression
# Supports:
# 1. Compression
# 2. Decompression
# 3. Binary Tags
# 4. Overlapping Matches
# 5. Text Files
# ============================================================


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

WINDOW_SIZE = 32
LOOKAHEAD_SIZE = 16

INPUT_FILE = "file1.txt"
COMPRESSED_FILE = "file2.txt"
DECOMPRESSED_FILE = "file3.txt"


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------

def int_to_binary(number, bits):
    """
    Convert an integer to a fixed-size binary string.
    Example:
        int_to_binary(5, 4) -> '0101'
    """
    return format(number, f"0{bits}b")


def binary_to_int(binary):
    """
    Convert binary string to integer.
    """
    return int(binary, 2)


def get_position_bits():
    """
    Number of bits needed to represent positions
    inside the sliding window.
    """
    return max(1, (WINDOW_SIZE).bit_length())


def get_length_bits():
    """
    Number of bits needed to represent match lengths.
    """
    return max(1, (LOOKAHEAD_SIZE).bit_length())


# ------------------------------------------------------------
# Find Longest Match
# ------------------------------------------------------------

def find_longest_match(data, current_position):
    """
    Find the longest match between the lookahead buffer
    and the search buffer.

    This function supports OVERLAPPING matches.

    Returns:
        (position, length)
    """

    start = max(0, current_position - WINDOW_SIZE)

    end = min(
        len(data),
        current_position + LOOKAHEAD_SIZE
    )

    best_position = 0
    best_length = 0

    # Search inside the sliding window
    for search_position in range(start, current_position):

        length = 0

        # Try to extend the match
        while (
            length < LOOKAHEAD_SIZE
            and current_position + length < len(data)
        ):

            # ------------------------------------------------
            # IMPORTANT:
            # We intentionally allow the source position
            # to move into the part being generated.
            #
            # This is what allows OVERLAPPING matches.
            # ------------------------------------------------

            source_position = search_position + length

            if source_position >= len(data):
                break

            if data[source_position] != data[current_position + length]:
                break

            length += 1

        if length > best_length:
            best_length = length
            best_position = current_position - search_position

    return best_position, best_length


# ------------------------------------------------------------
# Compression
# ------------------------------------------------------------

def compress_text(text):
    """
    Compress text using LZ77.

    Each tag has the form:

        <Position, Length, Next Symbol>

    Position  -> binary
    Length    -> binary
    Symbol    -> 8-bit binary
    """

    data = text.encode("utf-8")

    position_bits = get_position_bits()
    length_bits = get_length_bits()

    tags = []

    current_position = 0

    while current_position < len(data):

        position, length = find_longest_match(
            data,
            current_position
        )

        # ----------------------------------------------------
        # If no match was found
        # ----------------------------------------------------

        if length == 0:

            position = 0
            length = 0

            next_symbol = data[current_position]

            current_position += 1

        # ----------------------------------------------------
        # Match was found
        # ----------------------------------------------------

        else:

            next_position = current_position + length

            # If the match reaches the end of the file,
            # there is no next symbol.
            if next_position < len(data):
                next_symbol = data[next_position]
                current_position = next_position + 1

            else:
                # We need a special value for "no next symbol".
                next_symbol = None
                current_position = next_position

        # ----------------------------------------------------
        # Convert tag to Binary
        # ----------------------------------------------------

        position_binary = int_to_binary(
            position,
            position_bits
        )

        length_binary = int_to_binary(
            length,
            length_bits
        )

        if next_symbol is None:

            symbol_binary = "00000000"

            has_symbol = "0"

        else:

            symbol_binary = int_to_binary(
                next_symbol,
                8
            )

            has_symbol = "1"

        # ----------------------------------------------------
        # Complete Binary Tag
        #
        # Format:
        #
        # [has_symbol][position][length][symbol]
        # ----------------------------------------------------

        binary_tag = (
            has_symbol
            + position_binary
            + length_binary
            + symbol_binary
        )

        tags.append(binary_tag)

    return tags


# ------------------------------------------------------------
# Save Binary Tags
# ------------------------------------------------------------

def save_compressed_file(tags, filename):
    """
    Save all LZ77 tags as binary strings in file2.txt.

    Metadata is stored at the beginning so that the
    decompressor knows the field sizes.
    """

    position_bits = get_position_bits()
    length_bits = get_length_bits()

    with open(filename, "w", encoding="utf-8") as file:

        # Header
        file.write("LZ77\n")
        file.write(f"POSITION_BITS={position_bits}\n")
        file.write(f"LENGTH_BITS={length_bits}\n")

        file.write("TAGS\n")

        # Write every tag
        for tag in tags:
            file.write(tag + "\n")


# ------------------------------------------------------------
# Read Binary Tags
# ------------------------------------------------------------

def read_compressed_file(filename):
    """
    Read binary tags from file2.txt.
    """

    with open(filename, "r", encoding="utf-8") as file:

        lines = file.read().splitlines()

    # Validate header
    if lines[0] != "LZ77":
        raise ValueError("Invalid LZ77 compressed file.")

    position_bits = int(
        lines[1].split("=")[1]
    )

    length_bits = int(
        lines[2].split("=")[1]
    )

    tags_start = lines.index("TAGS") + 1

    tags = lines[tags_start:]

    return tags, position_bits, length_bits


# ------------------------------------------------------------
# Decompression
# ------------------------------------------------------------

def decompress_tags(tags, position_bits, length_bits):
    """
    Decompress LZ77 binary tags.

    The important part here is the copying loop.

    It copies ONE BYTE AT A TIME.

    This automatically handles overlapping matches.
    """

    output = bytearray()

    for tag in tags:

        index = 0

        # ----------------------------------------------------
        # Read has_symbol flag
        # ----------------------------------------------------

        has_symbol = tag[index]

        index += 1

        # ----------------------------------------------------
        # Read Position
        # ----------------------------------------------------

        position_binary = tag[
            index:
            index + position_bits
        ]

        index += position_bits

        position = binary_to_int(
            position_binary
        )

        # ----------------------------------------------------
        # Read Length
        # ----------------------------------------------------

        length_binary = tag[
            index:
            index + length_bits
        ]

        index += length_bits

        length = binary_to_int(
            length_binary
        )

        # ----------------------------------------------------
        # Read Next Symbol
        # ----------------------------------------------------

        symbol_binary = tag[index:index + 8]

        next_symbol = binary_to_int(
            symbol_binary
        )

        # ----------------------------------------------------
        # Copy matched data
        #
        # IMPORTANT:
        #
        # Do NOT copy the whole substring at once.
        #
        # Copy one byte at a time.
        #
        # This supports overlapping matches.
        # ----------------------------------------------------

        if position > 0 and length > 0:

            start = len(output) - position

            for i in range(length):

                # ------------------------------------------------
                # The source can be a byte that we just appended.
                #
                # This is the overlapping behavior.
                # ------------------------------------------------

                output.append(
                    output[start + i]
                )

        # ----------------------------------------------------
        # Add next symbol
        # ----------------------------------------------------

        if has_symbol == "1":
            output.append(next_symbol)

    return bytes(output)


# ------------------------------------------------------------
# Decompression to File
# ------------------------------------------------------------

def decompress_file(compressed_filename, output_filename):
    """
    Read file2.txt, decompress it,
    and write the original data to file3.txt.
    """

    tags, position_bits, length_bits = read_compressed_file(
        compressed_filename
    )

    decompressed_data = decompress_tags(
        tags,
        position_bits,
        length_bits
    )

    with open(
        output_filename,
        "wb"
    ) as file:

        file.write(decompressed_data)


# ------------------------------------------------------------
# Compress File
# ------------------------------------------------------------

def compress_file(input_filename, output_filename):
    """
    Read file1.txt and create file2.txt.
    """

    with open(
        input_filename,
        "r",
        encoding="utf-8"
    ) as file:

        text = file.read()

    tags = compress_text(text)

    save_compressed_file(
        tags,
        output_filename
    )


# ------------------------------------------------------------
# Verify Decompression
# ------------------------------------------------------------

def verify_files(original_filename, decompressed_filename):
    """
    Check whether decompression produced
    exactly the original file.
    """

    with open(
        original_filename,
        "rb"
    ) as original:

        original_data = original.read()

    with open(
        decompressed_filename,
        "rb"
    ) as decompressed:

        decompressed_data = decompressed.read()

    return original_data == decompressed_data


# ------------------------------------------------------------
# Menu
# ------------------------------------------------------------

def menu():

    while True:

        print("\n" + "=" * 50)
        print("             LZ77 DATA COMPRESSION")
        print("=" * 50)

        print("1. Compress file1.txt")
        print("2. Decompress file2.txt")
        print("3. Compress then Decompress")
        print("4. Exit")

        choice = input("\nEnter your choice: ")

        # ----------------------------------------------------
        # Compression
        # ----------------------------------------------------

        if choice == "1":

            try:

                compress_file(
                    INPUT_FILE,
                    COMPRESSED_FILE
                )

                print("\nCompression completed successfully.")
                print(f"Input file      : {INPUT_FILE}")
                print(f"Compressed file : {COMPRESSED_FILE}")

            except Exception as e:

                print("\nCompression failed.")
                print("Error:", e)

        # ----------------------------------------------------
        # Decompression
        # ----------------------------------------------------

        elif choice == "2":

            try:

                decompress_file(
                    COMPRESSED_FILE,
                    DECOMPRESSED_FILE
                )

                print("\nDecompression completed successfully.")
                print(f"Compressed file   : {COMPRESSED_FILE}")
                print(f"Decompressed file : {DECOMPRESSED_FILE}")

                if verify_files(
                    INPUT_FILE,
                    DECOMPRESSED_FILE
                ):
                    print("\nVerification: SUCCESS")
                    print("The decompressed file is identical to file1.txt.")

                else:
                    print("\nVerification: FAILED")
                    print("The files are not identical.")

            except Exception as e:

                print("\nDecompression failed.")
                print("Error:", e)

        # ----------------------------------------------------
        # Compression + Decompression
        # ----------------------------------------------------

        elif choice == "3":

            try:

                compress_file(
                    INPUT_FILE,
                    COMPRESSED_FILE
                )

                print("\nCompression completed.")

                decompress_file(
                    COMPRESSED_FILE,
                    DECOMPRESSED_FILE
                )

                print("Decompression completed.")

                if verify_files(
                    INPUT_FILE,
                    DECOMPRESSED_FILE
                ):
                    print("\nVerification: SUCCESS")
                    print("Original == Decompressed")

                else:
                    print("\nVerification: FAILED")

            except Exception as e:

                print("\nOperation failed.")
                print("Error:", e)

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        elif choice == "4":

            print("\nGoodbye!")
            break

        else:

            print("\nInvalid choice. Please choose 1-4.")


# ------------------------------------------------------------
# Program Entry Point
# ------------------------------------------------------------

if __name__ == "__main__":
    menu()