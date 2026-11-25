#!/bin/bash
echo "Content-Type: text/html"
echo ""
python3 milestone_udp_gen.py
echo '<br><button onclick="history.back()">Back</button>'