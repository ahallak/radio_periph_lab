#!/bin/bash
echo "Content-Type: text/html"
echo ""
echo "Starting FIFO reader..."
kill -STOP $(ps | grep '[p]ython3 run.py' | awk '{print $1}')
python3 milestone_fifo_rd.py
kill -CONT $(ps | grep '[p]ython3 run.py' | awk '{print $1}')
echo '<br><button onclick="history.back()">Back</button>'
