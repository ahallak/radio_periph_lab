import socket, struct, sys, time, os, mmap
import numpy as np
import json

try:
    with open("ip_cfg.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        dst_ip = data["ip"]
        port = int(data["port"])
except Exception as e:
    print(e)
    dst_ip = '169.254.1.10'
    port = 25344

if(len(sys.argv) > 1):
    dst_ip = sys.argv[1]
if(len(sys.argv) > 2):
    port = int(sys.argv[2])

print(f"Stream Destination IP: {dst_ip}, PORT: {port}")
    
S2MM_FIFO_ADDR    = 0x43C10000
RADIO_PERIPH_ADDR = 0x43C00000

RADIO_CTL_OFFSET   = 0x8
FIFO_OCCUPANCY_REG = 0x1C
FIFO_RESET_REG     = 0x28
FIFO_RESET_KEY     = 0xA5
FIFO_POP_OFFSET    = 0x20

COMPLEX_SAMPS_PER_PKT = 256

def open_mem(addr):
    try:
        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    except PermissionError:
        print("Error: You must run this script as root (sudo).", file=sys.stderr)
        exit(-1)
    try:
        page_size = os.sysconf('SC_PAGE_SIZE')
        # This probably varies based on page size. But our platform isn't changing soo.. gonna
        # keep this hardcoded.
        address = addr & 0xFFFF0000
        mem = mmap.mmap(fd, page_size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=address)
        os.close(fd)
        return mem
    
    except Exception as e:
        print(e)
        exit(-1)

def write_mem(addr, data):
    mem = open_mem(addr)
    offset = addr & 0xFFFF
    mem[offset : offset + 4] = data.to_bytes(4, byteorder='little')
    mem.close()

def check_udp_enabled():
    val_b = radio_mem[RADIO_CTL_OFFSET : RADIO_CTL_OFFSET + 4]
    val = int.from_bytes(val_b, byteorder='little', signed=False)
    return not((val >> 1) & 1)

def read_occupancy():
    val_b = fifo_mem[FIFO_OCCUPANCY_REG : FIFO_OCCUPANCY_REG + 4]
    val = int.from_bytes(val_b, byteorder='little', signed=False)
    return val

def read_fifo(occupancy):
    for each in range(0,occupancy):
        val_b = fifo_mem[FIFO_POP_OFFSET : FIFO_POP_OFFSET + 4]
        val_b = val_b[2:] + val_b[:2]
        word = int.from_bytes(val_b, byteorder='little', signed=False)
        buf[each] = word
    return buf

buf = np.empty(COMPLEX_SAMPS_PER_PKT, dtype=np.uint32)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#print("Reset key to fifo...")
write_mem(S2MM_FIFO_ADDR + FIFO_RESET_REG, FIFO_RESET_KEY)
# Configure FIFO
write_mem(S2MM_FIFO_ADDR,0xFFFFFFFF)

fifo_mem = open_mem(S2MM_FIFO_ADDR)
radio_mem = open_mem(RADIO_PERIPH_ADDR)

occupancy = read_occupancy()
#print(f"Flushing {occupancy} stale samples from FIFO...")
read_fifo(occupancy)

def get_payload(nWords):
    total = 0
    while(1):
        occupancy = read_occupancy()
        if(occupancy > nWords):
            if((total + occupancy) >= nWords):
                occupancy -= total+occupancy-nWords
            d = read_fifo(occupancy)
            total += occupancy
        if(total >= nWords):
            return d

try:
    count = 0
    while True:
        if(check_udp_enabled()):
            samples = get_payload(COMPLEX_SAMPS_PER_PKT)
            # <i = little endian, int (32b)
            payload = struct.pack('<i', count) + samples.tobytes()
            sock.sendto(payload, (dst_ip, port))
            count += 1
        else:
            print("UDP is currently disabled...")
            time.sleep(1)
except Exception as e:
    print("<br>*****ERROR.******** Check IP and port...<br>")
    print(e)
finally:
    # make sure we kill the socket if we ctrl+c out of the program
    sock.close()