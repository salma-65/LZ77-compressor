def overlap_match(data, candidate, current, max_length ):
    distance = current - candidate

    #setting a limit for the function
    limit = min(len(data) - current, max_length)
    length = 0
    while length < limit: 
        if length >= distance: #overlap condition
            source = candidate + (length % distance)
        else:
            source = candidate + length
        if data[source] != data[current + length]:
            break
        length+= 1
    return length

# # test 1
# data = "BBBBBBBBBB"
# result = overlap_match(data, 0, 1, 9)
# print(result)

# # test 2
# data = "ABABABAB"
# result = overlap_match(data, 0, 2, 6)
# print(result)

# # test 3
# data = "ABCABCABCX"
# result = overlap_match(data, 0, 3, 7)
# print(result) #6

# data = "ABABABAB"

# result = overlap_match(data, 0, 2, 6)

# print("Position:", 2)
# print("Length:", result)
    

