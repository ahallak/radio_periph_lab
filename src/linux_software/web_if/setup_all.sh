#!/bin/bash
echo "Content-type: text/html" # Tells the browser what kind of content to expect
echo "" # An empty line. Mandatory, if it is missed the page content will not load
echo "<p><em>"
echo "loading PL...<br>"
kill -9 $(ps | grep '[p]ython3 run.py' | awk '{print $1}')
fpgautil -b design_1_wrapper.bit.bin
echo "</p></em><p>"
echo "configuring Codec...<br>"
./configure_codec.sh
echo "</p>"
echo "Starting UDP Streamer Program...<br>"
python3 run.py > /dev/null 2>&1 < /dev/null &
echo "<p><em>All Done!</em></p>" 
echo '<br><button onclick="history.back()">Back</button>'