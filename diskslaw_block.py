from os import path,scandir
from sys import stderr
from subprocess import Popen,PIPE

#Write out validation items
def create_validation_text(validation_string,device):
    validation_device_path = '/dev/'+device
    if path.exists(validation_device_path):
        with open(validation_device_path,'w+') as validation_device:
            try:
                #Write text to the beginning
                validation_device.seek(0)
                validation_device.write(validation_string)
                #Check for the string at the end of the device
                validation_device.seek(get_disk_size(device)-len(validation_string))
                validation_device.write(validation_string)
                #Check for the string one third of the way through the device
                validation_device.seek(int(get_disk_size(device)/3)-len(validation_string))
                validation_device.write(validation_string)
            except:
                print('Error writing validation'+device,file=stderr)
    (all_there,_) = validate_text(validation_string,device)
    return all_there

#Helper function to get disk size
def get_disk_size(device):
    size = -1
    size_bo_path = '/sys/block/'+device+'/size'
    if path.exists(size_bo_path):
        with open(size_bo_path,'r') as block_size_fo:
            try:
                block_size_str = block_size_fo.read()
                if(int(block_size_str) > 0):
                    size = int(block_size_str)*512
            except:
                print('Error getting disk size for '+device,file=stderr)
    return size

#Validates the text on the device
def validate_text(validation_string,device):
    strings_present = 0
    validation_device_path = '/dev/'+device
    if path.exists(validation_device_path):
        with open(validation_device_path,'rb') as validation_device:
            try:
                #Check that the text is at the beginning
                validation_device.seek(0)
                if str(validation_device.read(len(validation_string)),'UTF-8') == validation_string:
                    strings_present+= 1
                #Check for the string at the end of the device
                validation_device.seek(get_disk_size(device)-len(validation_string))
                if str(validation_device.read(len(validation_string)),'UTF-8') == validation_string:
                    strings_present+= 1
                #Check for the string one third of the way through the device
                validation_device.seek(int(get_disk_size(device)/3)-len(validation_string))
                if str(validation_device.read(len(validation_string)),'UTF-8') == validation_string:
                    strings_present+= 1
            except:
                print('Error validating '+device,file=stderr)
    validated_all = False
    validated_missing = False
    if strings_present == 0:
        validated_missing = True
    if strings_present == 3:
        validated_all = True
    return validated_all,validated_missing

# Gets a tuple of lists of valid devices, skipped devices, and why the devices were skipped
def get_valid_devices(devices_to_skip,models_to_skip,skip_removable=True):
    skipped_devices = []
    valid_devices = []
    skipped_reason = []
    for entry in scandir('/sys/block/'):
        #Check if we should explicitly skip it
        if not entry.name in devices_to_skip:
            #Check if the model is one we should skip
            with open('/sys/block/'+entry.name+'/device/model') as model_fo:
                model = model_fo.read().strip()
                for checked_model in models_to_skip:
                    if checked_model in model.lower() and not entry.name in skipped_devices:
                        skipped_devices.append(entry.name)
                        skipped_reason.append("Model \""+model.lower()+"\" matched \""+checked_model+"\"")
            #Make sure model check didn't add the device to skipped devices
            if not entry.name in skipped_devices:
                #Check if the device is read-only
                if get_sys_block_property_int((entry.name),'ro') != 0:
                    skipped_devices.append(entry.name)
                    skipped_reason.append("Device is read only")

            #Make sure read only check didn't add the device to skipped devices
            if not entry.name in skipped_devices:
                #Check if the device is 0 size
                if get_sys_block_property_int((entry.name),'size') == 0:
                    skipped_devices.append(entry.name)
                    skipped_reason.append("Device has no length")

            #Make sure size check didn't add the device to skipped devices
            if not entry.name in skipped_devices and skip_removable == True:
                #Check if the device is removable
                if get_sys_block_property_int((entry.name),'removable') != 0:
                    skipped_devices.append(entry.name)
                    skipped_reason.append("Device is removable")

            #Make sure removable check didn't add the device to skipped devices
            if not entry.name in skipped_devices:
                #Check if the device can't be opened (Ex: Empty DVD drive or read only DVD)
                try:
                  with open('/dev/'+entry.name,'w') as opencheck_fo:
                    valid_devices.append(entry.name)
                    opencheck_fo.close()
                except:
                    skipped_devices.append(entry.name)
                    skipped_reason.append("Could not open device for write")
        else:
            skipped_devices.append(entry.name)
            skipped_reason.append("Explicitly listed to skip by config")
    return valid_devices,skipped_devices,skipped_reason

def get_sys_block_property_int(device,path):
    with open('/sys/block/'+device+'/'+path) as prop_fo:
        prop= int(prop_fo.read().strip())
        return prop

def get_rotational(device):
    rotates = True
    if get_sys_block_property_int(device,'queue/rotational') != 1:
        rotates = False
    return rotates

def get_secure_erase(device):
    secure_erasable = False
    hdparm_p = Popen(['hdparm','-I',('/dev/'+device)],stdout=PIPE)
    (hdparm_out,_) = hdparm_p.communicate()
    if 'supported: enhanced erase' in hdparm_out:
        secure_erasable = True
    return secure_erasable

def get_drive_frozen(device):
    frozen = True
    hdparm_p = Popen(['hdparm','-I',('/dev/'+device)],stdout=PIPE)
    (hdparm_out,_) = hdparm_p.communicate()
    if 'not\tfrozen' in hdparm_out:
        frozen = False
    return frozen

def get_drive_has_master_password(device):
    has_master_password = True
    hdparm_p = Popen(['hdparm','-I',('/dev/'+device)],stdout=PIPE)
    (hdparm_out,_) = hdparm_p.communicate()
    if 'not\tenabled' in hdparm_out:
        has_master_password = False
    return has_master_password

def get_secure_erase_time(device):
    secure_erase_time=5
    hdparm_p = Popen(['hdparm','-I',('/dev/'+device)],stdout=PIPE)
    (hdparm_out,_) = hdparm_p.communicate()
    if 'supported: enhanced erase' in hdparm_out:
        for line in hdparm_out.split('\n'):
            if 'SECURITY ERASE UNIT' in line and 'min' in line:
                secure_erase_time = int(line.strip().split('min')[0])
    return secure_erase_time