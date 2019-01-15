#!/usr/bin/env python3

#Imports
from yaml import safe_load
from dialog import Dialog
from os import path
from datetime import datetime
from diskslaw_power_management import disable_terminal_blanking,suspend_computer
from diskslaw_block import create_validation_text,validate_text,get_valid_devices,get_drive_frozen
from diskslaw_erase import disk_eraser
from sys import stderr

#Defaults
ds_config_file_path = "/etc/diskslaw/main.yml"
ds_config = {}

#Check if the config exists
if path.isfile(ds_config_file_path):
    #Load in the config
    ds_config_file_object = open(ds_config_file_path,'r')
    ds_config=safe_load(ds_config_file_object)


#Function for formatting the output
def ds_output(item,status,path,delimeter='\t'):
    with open(path,'a') as ds_append_fo:
        with datetime.datetime.now() as now:
            ds_append_fo.write(''+item+delimeter+status+delimeter+now.isoformat())

#Where output should go
ds_output_file = '/tmp/DiskSlaw.out'
if 'output_file' in ds_config:
    ds_output_file = ds_config['output_file']

#Set default config for valid devices
devices_to_skip = []
models_to_skip = []
skip_removables = True
shred_method = 'zero'
shred_rounds = 1

#Load in config options
if 'skip_removable' in ds_config:
    skip_removables = bool(ds_config['skip_removable'])

if 'ignore_device_model_strings' in ds_config:
    models_to_skip = ds_config['ignore_device_model_strings']

if 'ignore_device_input_file' in ds_config:
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

#Get valid and skipped device following rules from the config
(valid_devices,skipped_devices,skipped_device_reason) = get_valid_devices(devices_to_skip,models_to_skip,skip_removables)

#Log out the skipped devices
index = 0
for device in skipped_devices:
    ds_output(device,'SKIPPED: '+skipped_device_reason[index],ds_output_file)
    index+=1

#Create the dialog
userDialog = Dialog(dialog="dialog",autowidgetsize=True)
userDialog.set_background_title("Drive Wipe")

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
userDialog.gauge_start("Starting disk wipe", 15,45)
wiping_threads = []
thread_disks = []
for i in range(len(valid_devices)):
    t = disk_eraser(valid_devices[i],shred_method,shred_rounds)
    t.start()
    wiping_threads.append(t)
    thread_disks.append(valid_devices[i])
    userDialog.gauge_update((int((i/len(valid_devices))*100)))
userDialog.gauge_stop()

userDialog.gauge_start("Wiping disks", 15,45)
#Display a GUI until all threads finish
allThreadsFinished = False
while allThreadsFinished == False:
    threadsRunning = 0
    disks_completed = []
    disks_wiping = []
    #Count threads still running
    for i in range(len(wiping_threads)):
        if(wiping_threads[i].is_alive):
            threadsRunning+=1
            disks_wiping.append(thread_disks[i])
        else:
            disks_completed.append(thread_disks[i])
    if threadsRunning == 0:
        allThreadsFinished = True
    #Update dialog
    userDialog.gauge_update(len(disks_completed)/len(wiping_threads),"Wiping disks\n\nCompleted:"+(','.join(disks_completed))+"\n\nRunning:"+(','.join(disks_wiping)))

for device in wiping_threads:
    ds_output(device.wipe_device,""+device.wipe_type+":"+device.wipe_return_code,ds_output_file)