#!/usr/bin/env python3

#Imports
from yaml import safe_load
from dialog import Dialog
from os import path
from datetime import datetime
from diskslaw_power_management import disable_terminal_blanking,suspend_computer
from diskslaw_block import create_validation_text,validate_text,get_valid_devices,get_drive_frozen,get_secure_erase_time
from diskslaw_erase import disk_eraser
from sys import stderr
from time import sleep,monotonic
import re

#Defaults
ds_config_file_path = "/opt/diskslaw/main.yml"
ds_config = {}

#Check if the config exists
if path.isfile(ds_config_file_path):
    #Load in the config
    ds_config_file_object = open(ds_config_file_path,'r')
    ds_config=safe_load(ds_config_file_object)


#Function for formatting the output
def ds_output(item,status,details,filepath,return_code=0,time_spent=0,validated=False,delimeter='\t'):
    #If its a new file add the header row
    if not path.exists(filepath):
        with open(filepath,'w') as log_fo:
            log_fo.write('device'+delimeter+'status'+delimeter+'validated'+delimeter+'details'+delimeter+'return_code'+delimeter+'time_spent'+delimeter+'datetime\n')
    with open(filepath,'a') as ds_append_fo:
        ds_append_fo.write(''+item+delimeter+status+delimeter+str(validated)+delimeter+details+delimeter+str(return_code)+delimeter+str(time_spent)+delimeter+datetime.now().isoformat()+'\n')

#Where output should go
ds_output_file = '/tmp/DiskSlaw.out'
if 'output_file' in ds_config:
    ds_output_file = ds_config['output_file']

#Create the dialog
userDialog = Dialog(dialog="dialog",autowidgetsize=True)
userDialog.set_background_title("Drive Wipe")

#Set default config for valid devices
devices_to_skip = []
models_to_skip = []
skip_removables = True
shred_method = 'zero'
shred_rounds = 1
nvme_wipe_type = 1

#Load in config options
if 'skip_removable' in ds_config:
    skip_removables = bool(ds_config['skip_removable'])

if 'ignore_device_model_strings' in ds_config:
    models_to_skip = ds_config['ignore_device_model_strings']

if 'ignore_device_input_file' in ds_config:
    if path.isfile(ds_config['ignore_device_input_file']):
        with open(ds_config['ignore_device_input_file'],'r') as ignore_device_fo:
            devices_to_skip = ignore_device_fo.readlines()

if 'shred_method' in ds_config:
    if ds_config['shred_method'] == 'zero':
        shred_method = 'zero'
    else:
        shred_method = 'random'

if 'shred_rounds' in ds_config:
    try:
        if int(ds_config['shred_rounds'] ) > 1:
            shred_rounds = int(ds_config['shred_rounds'])
    except:
        print("ERROR reading shred rounds",file=stderr)

# There's only two actually valid wipe types for NVMe, 1 and 2
if 'nvme_wipe_type' in ds_config:
    try:
        if int(ds_config['nvme_wipe_type'] ) > 0 and int(ds_config['nvme_wipe_type'] ) < 3:
            nvme_wipe_type = int(ds_config['nvme_wipe_type'])
    except:
        print("ERROR reading nvme_wipe_type",file=stderr)

#Get valid and skipped device following rules from the config
(valid_devices,skipped_devices,skipped_device_reason) = get_valid_devices(devices_to_skip,models_to_skip,skip_removables)

#Log out the skipped devices
index = 0
for device in skipped_devices:
    ds_output(device,'skipped',skipped_device_reason[index],ds_output_file)
    index+=1



#Check for any frozen drives
anyDeviceFrozen = False
for dev in valid_devices:
    if get_drive_frozen(dev) == True:
        anyDeviceFrozen = True
#If there are frozen drives, suspend the machine to unfreeze them
if anyDeviceFrozen == True:
    userDialog.msgbox("A frozen SSD was found. I will need to go to sleep mode to unfreeze it. Press OK then wait a few seconds for the machine to fall asleep. Then press a keyboard key to wake it back up.")
    suspend_computer()

#Wipe the drive
userDialog.gauge_start("Starting disk wipe", 15,45,0,ascii_lines=True)
wiping_threads = []
for i in range(len(valid_devices)):
    t = disk_eraser(valid_devices[i],shred_method,shred_rounds,nvme_wipe_type)
    t.start()
    wiping_threads.append(t)
    userDialog.gauge_update((int((i/len(valid_devices))*100)))
userDialog.gauge_stop()

userDialog.gauge_start("Wiping disks", 15,45,0,ascii_lines=True)
#Display a GUI until all threads finish
allThreadsFinished = False
start_time = monotonic()
shred_re = re.compile('([0-9]+)/([0-9]+).* ([0-9]+)%')
while allThreadsFinished == False:
    threadsRunning = 0
    disks_completed = []
    disks_wiping = []
    #Count threads still running
    for i in range(len(wiping_threads)):
        if(wiping_threads[i].is_alive()):
            threadsRunning+=1
            try:
                eta = ' '
                if wiping_threads[i].device_expected_wipe_type == 'secure erase':
                    se_time = get_secure_erase_time(wiping_threads[i].wipe_device)
                    elapsed = monotonic()-start_time
                    eta = str(int(elapsed/se_time))+'%'
                if eta == ' ' and path.exists('/tmp/diskslaw_shred_'+wiping_threads[i].wipe_device+'.log'):
                    with open('/tmp/diskslaw_shred_'+wiping_threads[i].wipe_device+'.log','r') as dl:
                        lines = dl.readlines()
                        lines.reverse()
                        for line in lines:
                            if '%' in line and eta == ' ':
                                matches = shred_re.findall(line)
                                if len(matches) == 1 and len(matches[0]) == 3:
                                    current_round,all_rounds,round_percent = matches[0]
                                    eta = str(int((float(current_round)/int(all_rounds))*int(round_percent)))+'%'

                if eta == ' ':
                    eta = '0%'
                disks_wiping.append(wiping_threads[i].wipe_device+'('+eta+') ')
            except:
                disks_wiping.append(wiping_threads[i].wipe_device)
        else:
            valid = '(F)'
            if wiping_threads[i].wipe_validated == True:
                valid = '(P)'
            disks_completed.append(wiping_threads[i].wipe_device+' '+valid)
    if threadsRunning == 0:
        allThreadsFinished = True
    
    #Update dialog
    userDialog.gauge_update(int((float(len(disks_completed))/len(wiping_threads))*100),"Wiping disks\n\nCompleted:"+(','.join(disks_completed))+"\n\nRunning:"+(','.join(disks_wiping)),True)
    sleep(2)

for device in wiping_threads:
    details = ''
    if device.wipe_type != device.device_expected_wipe_type:
        details = device.wipe_type+' was used instead of the anticipated '+device.device_expected_wipe_type
    ds_output(device.wipe_device,device.wipe_type,details,ds_output_file,device.wipe_return_code,int(device.wipe_time),device.wipe_validated)