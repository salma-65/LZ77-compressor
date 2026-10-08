def decode(tuples):
    output = []

    for offset, length, next_symbol in tuples:

        # Copy the matched characters
        if length > 0:
            start = len(output) - offset

            for i in range(length):
                output.append(output[start + i])

        # Add the next symbol
        if next_symbol is not None:
            output.append(next_symbol)

    return output
