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
