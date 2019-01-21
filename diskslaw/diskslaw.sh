#!/bin/bash
#Disable Console Messages, they break Dialog
dmesg -n 1

#Configure dialog to work correctly
export NCURSES_NO_UTF8_ACS=1

#Launch diskslaw if it hasn't launched before
if [ -f /tmp/DiskSlaw.ran ]; then
    clear
    /usr/sbin/dmidecode -t1
    python3 /opt/diskslaw/view_results.py /tmp/DiskSlaw.csv 25 device,status,validated,details
else
    touch /tmp/DiskSlaw.ran
    cd /opt/diskslaw/
    python3 /opt/diskslaw/diskslaw.py
    clear
    /usr/sbin/dmidecode -t1
    python3 /opt/diskslaw/view_results.py /tmp/DiskSlaw.csv 25 device,status,validated,details
fi
read -p "Press enter to continue. Press the power button to shut down."

#Delay to keep systemd from thinking we are crashing when we are too slow releasing enter
sleep 5
