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

    