#!/usr/bin/env python3

#Imports
from yaml import safe_load
from dialog import Dialog
from os import path
from datetime import datetime
from diskslaw_power_management import disable_terminal_blanking,suspend_computer
from diskslaw_block import create_validation_text,validate_text,get_valid_devices

#Defaults
ds_config_file_path = "/etc/DiskSlaw/main.yml"
ds_config = {}

#Check if the config exists
if path.isfile(ds_config_file_path):
    #Load in the config
    ds_config_file_object = open(ds_config_file_path,'r')
    ds_config=safe_load(ds_config_file_object)


#Function for formatting the output
def ds_output(item,status,path):
    with open(path,'a') as ds_append_fo:
        with datetime.datetime.now() as now:
            ds_append_fo.write(''+item+','+status+','+now.isoformat())

#Where output should go
ds_output_file = '/tmp/DiskSlaw.out'
if 'output_file' in ds_config:
    ds_output_file = ds_config['output_file']

#