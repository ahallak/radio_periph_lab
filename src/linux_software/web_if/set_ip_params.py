#! /usr/bin/python3
import cgi, cgitb
import sys
import subprocess
import os
import sys
import mmap
import time
import json

form = cgi.FieldStorage()

ipaddr  = form.getvalue('ip')
port  = int(form.getvalue('port'))

data = {
    "ip": ipaddr,
    "port": port
}


with open("ip_cfg.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4)

subprocess.run("kill -STOP $(ps | grep '[p]ython3 run.py' | awk '{print $1}')" , shell=True)
subprocess.Popen("python3 run.py", start_new_session=True, shell=True)

print ("Content-type:text/html")
print()
print ("<html>")
print ('<head>')
print ("<title>Change IP Configs</title>")
print ('</head>')
print ('<body>')
print ("Changed IP Configuration")
print ("IP = %s, Port = %d" %(ipaddr,port))
print ('<br><button onclick="history.back()">Back</button>')
print ('</body>')
print ('</html>')