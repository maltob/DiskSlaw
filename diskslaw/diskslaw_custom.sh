#!/bin/bash
#Get the passed in script
export CUSTOM_SCRIPT=`cat /proc/cmdline  | awk '{split($0,a," ");   for (arg in a){      if(index($arg, "CUSTOM_SCRIPT=") != 0) {print substr($arg,index($arg,"=")+1)}  } }'`

#Run dhcp
dhclient

 echo "Custom script found, downloading"
#If a custom script is provided, download it
mkdir -p /tmp/customWipeScript
curl -k -L ${CUSTOM_SCRIPT} -q > /tmp/customWipeScript/customScript

if [ -s /tmp/customWipeScript/customScript ]; then
    chmod +x /tmp/customWipeScript/customScript
    /tmp/customWipeScript/customScript
else
    ip addr
    read -p "Custom script $CUSTOM_SCRIPT was empty. Do I have an IP ?"
fi