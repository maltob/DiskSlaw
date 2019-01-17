#!/bin/bash
#Disable Console Messages, they break Dialog
dmesg -n 1

#Configure dialog to work correctly
export NCURSES_NO_UTF8_ACS=1

#Launch diskslaw if it hasn't launched before
if [ -f /tmp/DiskSlaw.ran ]; then
    bash
else
    touch /tmp/DiskSlaw.ran
    cd /opt/diskslaw/
    python3 /opt/diskslaw/diskslaw.py
fi

read -p "Press enter to continue"
#