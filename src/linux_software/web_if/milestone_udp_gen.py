import socket, struct, sys, os, mmap
import numpy as np

# Defaults
dst_ip = '169.254.1.10'
port = 25344
nPackets = 1000

RADIO_PERIPH_ADDR = 0x43C00000

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

def read_mem(addr,signed=False):
    mem = open_mem(addr)
    offset = addr & 0xFFFF
    val_b = mem[offset : offset + 4]
    val = int.from_bytes(val_b, byteorder='little', signed=signed)
    mem.close()
    return val

if(len(sys.argv) > 1):
    nPackets = int(sys.argv[1])
if(len(sys.argv) > 2):
    dst_ip = sys.argv[2]
if(len(sys.argv) > 3):
    port = int(sys.argv[3])

print("Saving current reg values")
saved_reg = read_mem(RADIO_PERIPH_ADDR + 0x8)

# Disable radio...
write_mem(RADIO_PERIPH_ADDR + 0x8, 0b110)

complex_samples_per_pkt = 256
samples_per_pkt = complex_samples_per_pkt * 2
bytes_per_sample = 2

bytes_pkt_cnt = 4

udp_pkt_bytes = bytes_pkt_cnt + bytes_per_sample * samples_per_pkt;

print("------------")
print("Amjed Hallak, - Lab 11 Milestone")
print(f"SENDING {nPackets} {udp_pkt_bytes} BYTE PACKETS TO {dst_ip} ON PORT {port}")
print("------------")

# Make some total dummy data. Note that this is completely nonsensical :) 
Fs = 48000
t = np.linspace(0,48, udp_pkt_bytes//2)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def gen_payload(i):
    samplesFlQ = np.sin(2*np.pi*(1000*i)*t/Fs)
    samplesFlI = np.cos(2*np.pi*(2000*i)*t/Fs)
    # Interleave lists..
    samplesFl = [i for pair in zip(samplesFlI, samplesFlQ) for i in pair]
    # Make output bigger..why not?
    samples = [int(50*i) for i in samplesFl]
    return samples

try:
    count = 0
    while True:
        samples = gen_payload((count//10) % 600)
        # this works nicely, despite looking unusual. I don't often use struct.
        # <i = little endian, int (32b)
        # <{udp_pkt_bytes}h packs each sample into 16b signed integer
        payload = struct.pack('<i', count) + struct.pack(f'<{udp_pkt_bytes}h', *samples)
        sock.sendto(payload, (dst_ip, port))
        #print(count)
        count += 1
        if(count > nPackets):
            sock.close()
            print(f"{nPackets} packets have been sent. Exiting")
            break
except Exception as e:
    print(e)
finally:
    # make sure we kill the socket if we ctrl+c out of the program
    sock.close()

print("Restoring saved reg values")
write_mem(RADIO_PERIPH_ADDR + 0x8, saved_reg)