from subprocess import call,Popen,PIPE,DEVNULL
from diskslaw_block import get_rotational,get_secure_erase,get_drive_has_master_password,get_secure_erase_time
from diskslaw_block import get_disk_size,create_validation_text,validate_text,get_enhanced_secure_erase_time
from time import sleep,monotonic
from math import floor
import threading

class disk_eraser(threading.Thread):
    #Result properies
    wipe_return_code=-1
    wipe_type=""
    wipe_device = ""
    wipe_validated = False
    wipe_time = -1
    device_expected_wipe_type = "shred"
    
    #Parameters
    mech_wipe_type = "zero"
    mech_wipe_rounds = 1
    nvme_wipe_type = 1
    always_shred = False
    attempt_enhanced_secure_erase = False
    always_shred_rotational = False

    #Lookup for NVM wipe
    nvme_wipe_lookup = ('None','Data','Cryptographic')
    
    def __init__(self,device,mechanical_wipe_type="zero",mechanical_rounds=1,nvme_wipe_type=1,always_shred=False,attempt_enhanced_secure_erase=False,always_shred_rotational=False):
        threading.Thread.__init__(self)
        self.mech_wipe_rounds = mechanical_rounds
        self.mech_wipe_type = mechanical_wipe_type
        self.wipe_device = device
        self.nvme_wipe_type = nvme_wipe_type
        self.always_shred = always_shred
        self.attempt_enhanced_secure_erase = attempt_enhanced_secure_erase
        self.always_shred_rotational = always_shred_rotational
        self.device_expected_wipe_type = disk_eraser.get_device_wipe_type(device,mechanical_wipe_type,nvme_wipe_type)

    def run(self):
        self.wipe(self.wipe_device,self.mech_wipe_type,self.mech_wipe_rounds)
    def nvme_wipe(self,device,wipe_type=1):
        retcode = call(['nvme','format',('/dev/'+device),'-s',str(wipe_type)],None,stdout=open('/tmp/diskslaw_nvme_'+device+'.log','w'),stderr=open('/tmp/diskslaw_nvme_err_'+device+'.log','w'))
        return retcode

    def sata_secure_erase(self,device,password,user='u',expected_time=0):
        retcode = call(['hdparm','--user-master',user,'--security-erase',password,('/dev/'+device)],None,stdout=open('/tmp/diskslaw_se_'+device+'.log','w'),stderr=open('/tmp/diskslaw_se_err_'+device+'.log','w'))
        return retcode

    def sata_enhanced_secure_erase(self,device,password,user='u',expected_time=0):
        retcode = call(['hdparm','--user-master',user,'--security-erase-enhanced',password,('/dev/'+device)],None,stdout=open('/tmp/diskslaw_se_enhanced_'+device+'.log','w'),stderr=open('/tmp/diskslaw_se_enhanced_err_'+device+'.log','w'))
        return retcode

    def sata_set_password(self,device,password,user='u'):
        retcode = call(['hdparm','--user-master',user,'--security-set-pass',password,('/dev/'+device)],None,stdout=DEVNULL,stderr=DEVNULL)
        return (retcode == 0)

    def sata_disable_password(self,device,password):
        retcode = call(['hdparm','--security-disable',password,('/dev/'+device)],None,stdout=DEVNULL,stderr=DEVNULL)
        return (retcode == 0)

    def shred_device(self,device,rounds=1):
        retcode = call(['shred',('-n '+str(rounds)),'--verbose',('/dev/'+device)],None,stdout=DEVNULL,stderr=open('/tmp/diskslaw_shred_'+device+'.log','w'))
        return (retcode)

    def zero_device(self,device,rounds=1):
        retcode = call(['shred',('-n '+str(rounds)),'--verbose','--random-source=/dev/zero',('/dev/'+device)],None,stdout=DEVNULL,stderr=open('/tmp/diskslaw_shred_'+device+'.log','w'))
        return (retcode)
    @staticmethod
    def get_device_wipe_type(device,mechanical_wipe_type,nvme_wipe_type,always_shred=False,always_shred_rotational=False,attempt_enhanced_secure_erase=False):
        value = ""
        
        if 'nvme' in device:
            value = "nvme "+disk_eraser.nvme_wipe_lookup[nvme_wipe_type]+" wipe"
        elif get_secure_erase(device) == True:
            if attempt_enhanced_secure_erase:
                value = 'enhanced secure erase'
            else:
                value = 'secure erase'
        else:
            value = mechanical_wipe_type
        
        #If we always shred we run the first pass using secure erase/nvme then shred
        if always_shred and value != mechanical_wipe_type :
            value += " + "+mechanical_wipe_type

        if always_shred_rotational == True and get_rotational(device) == True:
            value = mechanical_wipe_type

        return value

    def wipe(self,device,mechanical_wipe_type='zero',mechanical_rounds=1,validation_string='HECTORSPECTORFLETCHER'):
        #Write out text to make sure we know if it worked
        create_validation_text(validation_string,device)
        
        wipe_start = monotonic()
        if self.device_expected_wipe_type.startswith('nvme'):
            #NVMe drive, wipe
            self.wipe_type = ""
            nvme_ret = self.nvme_wipe(device,self.nvme_wipe_type)
            if nvme_ret == 0:
                nvme_se_text = self.nvme_wipe_lookup[self.nvme_wipe_type]
                self.wipe_type = "nvme "+nvme_se_text+" wipe"
                self.wipe_return_code = nvme_ret
            
            if nvme_ret != 0 or self.always_shred == True:
                #Fall back to shred
                if self.always_shred == True and self.wipe_type != "":
                    self.wipe_type += " + "
                if mechanical_wipe_type == 'zero':
                    self.wipe_return_code = self.zero_device(device,mechanical_rounds)
                    self.wipe_type += "zero"
                else:
                    self.wipe_return_code = self.shred_device(device,mechanical_rounds)
                    self.wipe_type += "shred"
        elif 'secure erase' in self.device_expected_wipe_type:
            #Supports secure erase, either a mechanical drive with encryption or an SSD
            #Set the password so we can wipe it, I've had better luck with calling it twice
            if get_drive_has_master_password(device) == False:
                self.sata_set_password(device,'NULL')
                sleep(1)
                self.sata_set_password(device,'pass')
                sleep(1)
            #Get the estimated amount of time to wipe
            estimated_time = get_secure_erase_time(device)
            #Get current time
            start_time = monotonic()
            self.wipe_type = ""
            #Wipe
            if self.attempt_enhanced_secure_erase == True:
                see_ret = self.sata_enhanced_secure_erase(device,'pass')
                if see_ret == 0:
                    estimated_time = get_enhanced_secure_erase_time(device)
                    self.wipe_type = "enhanced "
                    se_ret = see_ret
                else:
                    se_ret = self.sata_secure_erase(device,'pass')
            else:
                se_ret = self.sata_secure_erase(device,'pass')

            #Disable the drive password to unlock it
            self.sata_disable_password(device,'pass')

            #If secure erase failed, fall back to shred
            if se_ret != 0 or self.always_shred:
                if self.always_shred == True and se_ret == 0:
                    self.wipe_type += "secure erase + "
                else:
                    self.wipe_type = ""
                #Fall back to shred
                if mechanical_wipe_type == 'zero':
                    self.wipe_return_code = self.zero_device(device,mechanical_rounds)
                    self.wipe_type += "zero"
                else:
                    self.wipe_return_code = self.shred_device(device,mechanical_rounds)
                    self.wipe_type += "shred"
            else:
                #Get time elapsed
                elapsed = monotonic()-start_time
                #If we are far off from estimated time, sleep to allow the drive to finish up
                if(((estimated_time*60)) > (elapsed)):
                    sleep(int((estimated_time*60)-elapsed))
                self.wipe_return_code = se_ret
                self.wipe_type += "secure erase"
        else:
            #Mechanical Drive probably, doesn't support secure erase so write to it
            if mechanical_wipe_type == 'zero':
                self.wipe_return_code = self.zero_device(device,mechanical_rounds)
                self.wipe_type = "zero"
            else:
                self.wipe_return_code = self.shred_device(device,mechanical_rounds)
                self.wipe_type = "shred"
        #Check the text is gone
        _,wiped_validation = validate_text(validation_string,device)
        if wiped_validation == True:
            self.wipe_validated = True
        #Update the wipe time
        self.wipe_time = monotonic()-wipe_start