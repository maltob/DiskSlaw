#!/bin/bash
#Disable Console Messages, they break Dialog
dmesg -n 1

#Configure dialog to work correctly
export NCURSES_NO_UTF8_ACS=1
current_tty=$(tty)
view_results="python3 /opt/diskslaw/tools/view_results.py /tmp/DiskSlaw.csv 20 device,status,validated,wwid"
#If we are on TTY1 run diskslaw
if [[ $current_tty =~ "tty1" ]]; then
    #Launch diskslaw if it hasn't launched before
    if [ -f /tmp/DiskSlaw.ran ]; then
        clear
        /usr/sbin/dmidecode -t1
        ${view_results}
    else
        touch /tmp/DiskSlaw.ran
        cd /opt/diskslaw/
        python3 /opt/diskslaw/diskslaw.py
        clear
        /usr/sbin/dmidecode -t1
        ${view_results}
    fi
elif [[ $current_tty =~ "tty2" ]]; then
    #TTY2 shows the log files
    tail -f /tmp/*.log > /tmp/alllogs.tail &
    less +F /tmp/alllogs.tail
else 
    #TTY3 shows dstat
    dstat -dr --disk-util --disk-tps
fi
read -p "Press enter to continue. Press the power button to shut down."

#Delay to keep systemd from thinking we are crashing when we are too slow releasing enter
sleep 5
