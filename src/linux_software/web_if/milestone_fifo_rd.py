import os
import sys
import mmap
import time
import concurrent.futures

# Amjed H - EN 525.742 Lab 11?

S2MM_FIFO_ADDR    = 0x43C10000
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

def read_fifo(addr,occupancy,signed=False):
    mem = open_mem(addr)
    offset = addr & 0xFFFF
    for i in range(0,occupancy):
        val_b = mem[offset : offset + 4]
        val = int.from_bytes(val_b, byteorder='little', signed=signed)
    mem.close()
    return val

print("Startup")
print("Config radio")

#print(read_mem(RADIO_PERIPH_ADDR + 0xC))
print("Saving current reg values")
saved_reg = read_mem(RADIO_PERIPH_ADDR + 0x8)
saved_pinc0 = read_mem(RADIO_PERIPH_ADDR + 0x0)
saved_pinc1 = read_mem(RADIO_PERIPH_ADDR + 0x4)

write_mem(RADIO_PERIPH_ADDR + 0x8, 0x1)
write_mem(RADIO_PERIPH_ADDR + 0x8, 0b100)

#print(read_mem(RADIO_PERIPH_ADDR + 0xC))

write_mem(RADIO_PERIPH_ADDR + 0x0, 1000)
write_mem(RADIO_PERIPH_ADDR + 0x4, 2000)

print("Reset key to fifo...")
write_mem(S2MM_FIFO_ADDR + 0x28, 0xa5)
time.sleep(0.5)

isr = read_mem(S2MM_FIFO_ADDR)
#print('isr', bin(isr))
write_mem(S2MM_FIFO_ADDR,0xFFFFFFFF)
#isr = read_mem(S2MM_FIFO_ADDR)
#print('isr', bin(isr))

# RDFO

#rdfo = read_mem(S2MM_FIFO_ADDR + 0x1c)
#print('rdfo (occupancy)', hex(rdfo))

#rlr = read_mem(S2MM_FIFO_ADDR + 0x24)
#print('rlr', hex(rlr))

total = 0
print("read 480,000 32-bit words from the FIFO...")
while(1):
    occupancy = read_mem(S2MM_FIFO_ADDR + 0x1c)
    if(occupancy > 0):
        if((total + occupancy) >= 480000):
            occupancy -= total+occupancy-480000
        data = read_fifo(S2MM_FIFO_ADDR + 0x20,occupancy)
    total += occupancy
    if(total >= 480000):
        print(f"{total} words have been read. exiting")
        break
print("Restoring saved reg values")
write_mem(RADIO_PERIPH_ADDR + 0x8, saved_reg)
write_mem(RADIO_PERIPH_ADDR + 0x0, saved_pinc0)
write_mem(RADIO_PERIPH_ADDR + 0x4, saved_pinc1)