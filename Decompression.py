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

def write_decompressed_file(filename, data):

    with open(filename, "wb") as file:
        file.write(data)