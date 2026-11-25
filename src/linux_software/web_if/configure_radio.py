#! /usr/bin/python3
import cgi, cgitb
import sys
import subprocess
import os
import sys
import mmap
import time

# Create instance of FieldStorage
form = cgi.FieldStorage()

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

# Full reset
write_mem(RADIO_PERIPH_ADDR + 0x8, 0xF)
# Remove reset, keep FIFO and Audio disabled
write_mem(RADIO_PERIPH_ADDR + 0x8, 0b110)

# Get data from fields
adc_freq_hz  = int(form.getvalue('adc_freq_hz'))
tune_freq_hz  = int(form.getvalue('tune_freq_hz'))
streaming = form.getvalue('streaming')
audio = form.getvalue('audio')

en_stream = 1 if streaming == "streaming" else 0
en_audio  = 1 if audio == "audio" else 0

def tuneRadio(freq_hz):
    pinc = int((freq_hz)*(1<<27)/125.0e6)
    write_mem(RADIO_PERIPH_ADDR, pinc)
    
def tuneADC(freq_hz):
    pinc = int(freq_hz*(1<<27)/125.0e6)
    write_mem(RADIO_PERIPH_ADDR + 0x4, pinc)


# Send the result to the browser
print ("Content-type:text/html")
print()
print ("<html>")
print ('<head>')
print ("<title>Radio Configurator</title>")
print ('</head>')
print ('<body>')
print ("<h2>Radio Configurator</h2>")
print ("Setting up the radio now...")
print ("ADC Freq = %d, Tune Freq = %d" %(adc_freq_hz,tune_freq_hz))
tuneADC(adc_freq_hz)
print ("ADC tune successful...")
tuneRadio(tune_freq_hz)
print ("Radio tune successful...")

print(f"Audio state: {en_audio==1}, UDP stream state: {en_stream==1}<br>")

ctl_reg_val = (not en_audio) << 2 | (not en_stream) << 1
write_mem(RADIO_PERIPH_ADDR + 0x8, ctl_reg_val)
print ('<br><button onclick="history.back()">Back</button>')
print ('</body>')
print ('</html>')

