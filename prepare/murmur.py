import random

## This is the equivalent implementation to the MurmurHash3 in C++
## Note: the byteorder in $key$ must be little endian
def murmurhash3_32(key, seed=0x0):
    length = len( key )
    nblocks = int( length / 4 )
    h = seed
    ind = 0

    if (length > 3):
        for block_start in range( 0, nblocks * 4, 4 ):
            k = key[ block_start + 3 ] << 24 | \
                key[ block_start + 2 ] << 16 | \
                key[ block_start + 1 ] <<  8 | \
                key[ block_start + 0 ]
        
            k = ( 0xcc9e2d51 * k ) & 0xFFFFFFFF
            k = ( k << 15 | k >> 17 ) & 0xFFFFFFFF 
            k = ( 0x1b873593 * k ) & 0xFFFFFFFF
            
            h = h ^ k
            h  = ( h << 13 | h >> 19 ) & 0xFFFFFFFF
            h  = ( h * 5 + 0xe6546b64 ) & 0xFFFFFFFF
            ind = ind + 4

    if (length & 3 != 0):
        i = length & 3
        k = 0
        ind = ind + i - 1
        while True:
            k = k << 8
            k = k | key[ ind ]
            ind = ind - 1
            i = i - 1
            if i == 0:
                break
        k = ( 0xcc9e2d51 * k ) & 0xFFFFFFFF
        k = ( k << 15 | k >> 17 ) & 0xFFFFFFFF
        k = ( 0x1b873593 * k ) & 0xFFFFFFFF
        h = h ^ k

    h = h ^ length
    h ^= h >> 16
    h  = ( h * 0x85ebca6b ) & 0xFFFFFFFF
    h ^= h >> 13
    h  = ( h * 0xc2b2ae35 ) & 0xFFFFFFFF
    h ^= h >> 16
    
    return h

def ip_to_int(ipaddr):
    parts = [int(i) for i in ipaddr.split('.')]
    bytes_parts = parts[0].to_bytes(1, byteorder='big') + parts[1].to_bytes(1, byteorder='big') +\
                    parts[2].to_bytes(1, byteorder='big') + parts[3].to_bytes(1, byteorder='big')
    return int.from_bytes(bytes_parts, byteorder='big')

def load_seeds(seed, degree, num_clusters):
    random.seed(seed)

    tor_seeds = [[0 for j in range(degree)] for i in range(num_clusters)]
    for i in range(0, num_clusters):
        for j in range(0, degree):
            tor_seeds[i][j] = random.randint(0, 32767)
    agg_seeds = [[0 for j in range(degree)] for i in range(num_clusters)]
    for i in range(0, num_clusters):
        for j in range(0, degree):
            agg_seeds[i][j] = random.randint(0, 32767)

    return tor_seeds, agg_seeds

def ecmp_helper(size, seed, src_ip, src_port, dst_ip, dst_port):
    # this requires python3
    src_ip = ip_to_int(src_ip)
    dst_ip = ip_to_int(dst_ip)

    src_ip_bytes = (src_ip).to_bytes(4, byteorder='little')
    src_port_bytes = ((int)(src_port)).to_bytes(2, byteorder='little')
    dst_ip_bytes = (dst_ip).to_bytes(4, byteorder='little')
    dst_port_bytes = ((int)(dst_port)).to_bytes(2, byteorder='little')
    flow_bin = src_ip_bytes + src_port_bytes + dst_ip_bytes + dst_port_bytes
    hash_v = murmurhash3_32(flow_bin, seed)

    return ((hash_v % size) + size) % size
