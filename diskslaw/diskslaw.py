#!/usr/bin/env python3

#Imports
from yaml import safe_load
from dialog import Dialog
from os import path
from datetime import datetime
from diskslaw_power_management import disable_terminal_blanking,suspend_computer
from diskslaw_block import create_validation_text,validate_text,get_valid_devices,get_drive_frozen,get_secure_erase_time,get_wwid,get_model,get_vendor,reset_device
from diskslaw_erase import disk_eraser
from sys import stderr
from time import sleep,monotonic
from diskslaw_config import diskslaw_config
from diskslaw_erase_secure import disk_eraser_secure_erase
from diskslaw_erase_nvme import disk_eraser_nvme

#Defaults
ds_config_file_path = "/opt/diskslaw/main.yml"
ds_config_hash = {}

#Check if the config exists
if path.isfile(ds_config_file_path):
    #Load in the config
    ds_config_file_object = open(ds_config_file_path,'r')
    ds_config_hash=safe_load(ds_config_file_object)

def ds_log(line,filepath='/tmp/diskslaw_main.log'):
    with open(filepath,'a') as ds_append_fo:
        ds_append_fo.write(line+'\n')


#Function for formatting the output
def ds_output(item,status,details,filepath,return_code=0,time_spent=0,validated=False,delimeter='\t',vendor='',model='',wwid=''):
    #If its a new file add the header row
    if not path.exists(filepath):
        with open(filepath,'w') as log_fo:
            log_fo.write('device'+delimeter+'status'+delimeter+'validated'+delimeter+'details'+delimeter+'return_code'+delimeter+'time_spent'+delimeter+'vendor'+delimeter+'model'+delimeter+'wwid'+delimeter+'datetime\n')
    with open(filepath,'a') as ds_append_fo:
        ds_append_fo.write(''+item+delimeter+status+delimeter+str(validated)+delimeter+details+delimeter+str(return_code)+delimeter+str(time_spent)+delimeter+vendor+delimeter+model+delimeter+wwid+delimeter+datetime.now().isoformat()+'\n')

#Where output should go
ds_output_file = '/tmp/DiskSlaw.out'
if 'output_file' in ds_config_hash:
    ds_output_file = ds_config_hash['output_file']



#Set default config for valid devices
devices_to_skip = []
models_to_skip = []
skip_removables = True

ds_configuration = diskslaw_config()

#Load in config options
if 'skip_removable' in ds_config_hash:
    skip_removables = bool(ds_config_hash['skip_removable'])

if 'ignore_device_model_strings' in ds_config_hash:
    models_to_skip = ds_config_hash['ignore_device_model_strings']

if 'ignore_device_input_file' in ds_config_hash:
    if path.isfile(ds_config_hash['ignore_device_input_file']):
        with open(ds_config_hash['ignore_device_input_file'],'r') as ignore_device_fo:
            devices_to_skip = ignore_device_fo.readlines()

#Load in the configuration
ds_configuration.load_from_hash(ds_config_hash)

#Get valid and skipped device following rules from the config
(valid_devices,skipped_devices,skipped_device_reason) = get_valid_devices(devices_to_skip,models_to_skip,skip_removables)

#Log out the skipped devices
index = 0
for device in skipped_devices:
    ds_output(device,'skipped',skipped_device_reason[index],ds_output_file)
    ds_log('Skipping '+device+' because '+skipped_device_reason[index])
    index+=1

#Create the dialog
userDialog = Dialog(dialog="dialog",autowidgetsize=True)
userDialog.set_background_title("Drive Wipe")

#Check for any frozen drives, try to reset it first
anyDeviceFrozen = False
for dev in valid_devices:
    if get_drive_frozen(dev) == True:
        anyDeviceFrozen = True
        ds_log(''+dev+' is still frozen, will need to suspend' )
#If there are frozen drives, suspend the machine to unfreeze them
if anyDeviceFrozen == True:
    userDialog.msgbox("A frozen SSD was found. I will need to go to sleep mode to unfreeze it. Press OK then wait a few seconds for the machine to fall asleep. Then press a keyboard key to wake it back up.")
    ds_log("Going to sleep")
    suspend_computer()
    #Give it a few seconds to wake back up - XPS 13 returned to blinking screen after suspend
    sleep(5)
    ds_log("Recovered from sleep")



#Wipe the drive
#userDialog.clear()
ds_log("Starting wipes")
userDialog.gauge_start("Starting disk wipe", 15,45,0,ascii_lines=True)
wiping_threads = []
for i in range(len(valid_devices)):
    ds_log(disk_eraser.get_device_wipe_type(valid_devices[i],ds_configuration))
    if 'nvme' in (disk_eraser.get_device_wipe_type(valid_devices[i],ds_configuration)):
        ds_log("nvm "+valid_devices[i])
        t = disk_eraser_nvme(valid_devices[i],ds_configuration)
    elif 'secure ' in (disk_eraser.get_device_wipe_type(valid_devices[i],ds_configuration)):
        ds_log("security erase "+valid_devices[i])
        t = disk_eraser_secure_erase(valid_devices[i],ds_configuration)
    else:
        ds_log("shred "+valid_devices[i])
        t = disk_eraser(valid_devices[i],ds_configuration)
    t.start()
    wiping_threads.append(t)
    userDialog.gauge_update((int((i/len(valid_devices))*100)))
userDialog.gauge_stop()
ds_log("All wipes started")

ds_log("Awaiting wipes")
userDialog.gauge_start("Wiping disks", 15,45,0,ascii_lines=True)
#Display a GUI until all threads finish
allThreadsFinished = False
while allThreadsFinished == False:
    threadsRunning = 0
    disks_completed = []
    disks_wiping = []
    #Count threads still running
    for i in range(len(wiping_threads)):
        if(wiping_threads[i].is_alive()):
            threadsRunning += 1
            try:
                eta = ''
                eta = wiping_threads[i].get_wipe_progress()
                if eta == '':
                    eta = '0%'
                else:
                    eta = eta+'%'
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

ds_log("All wipes done")
for device in wiping_threads:
    details = ''
    if device.wipe_type != device.device_expected_wipe_type:
        details = 'Mismatch: '+device.wipe_type+' vs '+device.device_expected_wipe_type
    ds_output(device.wipe_device,device.wipe_type,details,ds_output_file,device.wipe_return_code,int(device.wipe_time),device.wipe_validated,vendor=get_vendor(device.wipe_device),model=get_model(device.wipe_device),wwid=get_wwid(device.wipe_device))