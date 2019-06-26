from subprocess import call,Popen,PIPE,DEVNULL
from diskslaw_block import get_rotational,get_disk_size,create_validation_text,validate_text, get_secure_erase, get_secure_erase_time, get_enhanced_secure_erase_time
from time import sleep,monotonic
from math import floor
import threading
from diskslaw_config import diskslaw_config

class disk_eraser(threading.Thread):
    #Result properies
    wipe_return_code=-1
    wipe_type=""
    wipe_device = ""
    wipe_validated = False
    wipe_time = -1
    device_expected_wipe_type = "shred"

    wipe_start = 0
    
    diskslaw_configuration = diskslaw_config()
  
    def __init__(self,device,diskslaw_configuration):
        threading.Thread.__init__(self)
        self.device_expected_wipe_type = disk_eraser.get_device_wipe_type(device,diskslaw_configuration)
        self.wipe_device = device
        self.diskslaw_configuration = diskslaw_configuration
        

    def run(self):
        self.wipe()
    
    def get_wipe_progress(self):
        eta = ''
        se_time = get_secure_erase_time(self.wipe_device)
        elapsed = monotonic()-self.wipe_start
        eta = str(int(elapsed/se_time))
        return eta

    def shred_device(self,device,rounds=1):
        retcode = call(['shred',('-n '+str(rounds)),'--verbose',('/dev/'+device)],None,stdout=DEVNULL,stderr=open('/tmp/diskslaw_shred_'+device+'.log','w'))
        return (retcode)

    def zero_device(self,device,rounds=1):
        retcode = call(['shred',('-n '+str(rounds)),'--verbose','--random-source=/dev/zero',('/dev/'+device)],None,stdout=DEVNULL,stderr=open('/tmp/diskslaw_shred_'+device+'.log','w'))
        return (retcode)
    @staticmethod
    def get_device_wipe_type(device,config):
        value = ""
        
        if 'nvme' in device:
            value = "nvme "+config.nvme_wipe_lookup[config.nvme_wipe_type]+" wipe"
        elif get_secure_erase(device):
            if config.attempt_enhanced_secure_erase:
                value = 'enhanced secure erase'
            else:
                value = 'secure erase'
        else:
            value = config.mech_wipe_type
        
        #If we always shred we run the first pass using secure erase/nvme then shred
        if config.always_shred and value != config.mech_wipe_type :
            value += " + "+config.mech_wipe_type

        if config.always_shred_rotational == True and get_rotational(device) == True:
            value = config.mech_wipe_type

        return value

    def mech_wipe(self):
        if self.diskslaw_configuration.mech_wipe_type == 'zero':
            return (self.zero_device(self.wipe_device,self.diskslaw_configuration.mech_wipe_rounds),'zero')
        else:
            return(self.shred_device(self.wipe_device,self.diskslaw_configuration.mech_wipe_rounds),'shred')
        

    def init_wipe(self):
        #Write out text to make sure we know if it worked
        create_validation_text(self.diskslaw_configuration.validation_text,self.wipe_device)
        
        self.wipe_start = monotonic()

    def end_wipe(self):
        #Check the text is gone
        _,wiped_validation = validate_text(self.diskslaw_configuration.validation_text,self.wipe_device)
        if wiped_validation == True:
            self.wipe_validated = True
        #Update the wipe time
        self.wipe_time = monotonic()-self.wipe_start

    def wipe(self):
        self.init_wipe()
         #Mechanical Drive probably, doesn't support secure erase so write to it
        
        (return_code,mech_wipe_type) = self.mech_wipe()
        self.wipe_return_code = return_code
        self.wipe_type = mech_wipe_type

        self.end_wipe()
        