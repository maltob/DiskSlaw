import diskslaw_erase
from time import sleep,monotonic
from subprocess import call,Popen,PIPE,DEVNULL
from diskslaw_block import get_rotational,get_secure_erase,get_drive_has_master_password,get_secure_erase_time
from diskslaw_block import get_disk_size,create_validation_text,validate_text,get_enhanced_secure_erase_time
from os import path
import re

class disk_eraser_secure_erase(diskslaw_erase.disk_eraser):
    def __init__(self,device,config):
        super().__init__(device,config)
    
    def sata_secure_erase(self,device,password,user='u'):
        retcode = call(['hdparm','--user-master',user,'--security-erase',password,('/dev/'+device)],None,stdout=open('/tmp/diskslaw_se_'+device+'.log','w'),stderr=open('/tmp/diskslaw_se_err_'+device+'.log','w'))
        return retcode

    def sata_enhanced_secure_erase(self,device,password,user='u'):
        retcode = call(['hdparm','--user-master',user,'--security-erase-enhanced',password,('/dev/'+device)],None,stdout=open('/tmp/diskslaw_se_enhanced_'+device+'.log','w'),stderr=open('/tmp/diskslaw_se_enhanced_err_'+device+'.log','w'))
        return retcode

    def sata_set_password(self,device,password,user='u'):
        retcode = call(['hdparm','--user-master',user,'--security-set-pass',password,('/dev/'+device)],None,stdout=DEVNULL,stderr=DEVNULL)
        return (retcode == 0)

    def sata_disable_password(self,device,password,user='u'):
        retcode = call(['hdparm','--user-master',user,'--security-disable',password,('/dev/'+device)],None,stdout=DEVNULL,stderr=DEVNULL)
        return (retcode == 0)

    def get_wipe_progress(self):
        eta = ''
        shred_re = re.compile('([0-9]+)/([0-9]+).* ([0-9]+)%')
        if path.exists('/tmp/diskslaw_shred_'+self.wipe_device+'.log'):
            with open('/tmp/diskslaw_shred_'+self.wipe_device+'.log','r') as dl:
                lines = dl.readlines()
                lines.reverse()
                for line in lines:
                    if '%' in line and eta == ' ':
                        matches = shred_re.findall(line)
                        if len(matches) == 1 and len(matches[0]) == 3:
                            current_round,all_rounds,round_percent = matches[0]
                            eta = str(int((float(current_round)/int(all_rounds))*int(round_percent)))
        return eta

    def wipe(self):
        wipe_started = self.init_wipe()
        if wipe_started == True:
            #Supports secure erase, either a mechanical drive with encryption or an SSD
            #Set the password so we can wipe it, I've had better luck with calling it twice
            self.sata_set_password(self.wipe_device,'NULL')
            sleep(1)
            self.sata_set_password(self.wipe_device,'pass')
            sleep(1)
            #Get the estimated amount of time to wipe
            estimated_time = get_secure_erase_time(self.wipe_device)
            #Get current time
            self.wipe_type = ""
            #Wipe
            if self.diskslaw_configuration.attempt_enhanced_secure_erase == True:
                see_ret = self.sata_enhanced_secure_erase(self.wipe_device,'pass')
                _,wiped_validation = validate_text(self.diskslaw_configuration.validation_text,self.wipe_device)
                if see_ret == 0 and wiped_validation == True:
                    estimated_time = get_enhanced_secure_erase_time(self.wipe_device)
                    self.wipe_type = "enhanced "
                    se_ret = see_ret
                else:
                    se_ret = self.sata_secure_erase(self.wipe_device,'pass')
            else:
                se_ret = self.sata_secure_erase(self.wipe_device,'pass')

            #Disable the drive password to unlock it
            self.sata_disable_password(self.wipe_device,'pass')

            #If secure erase failed, fall back to shred
            if se_ret != 0 or self.diskslaw_configuration.always_shred:
                if self.diskslaw_configuration.always_shred == True and se_ret == 0:
                    self.wipe_type += "secure erase + "
                else:
                    self.wipe_type = ""
                #Fall back to shred
                if self.diskslaw_configuration.mech_wipe_type == 'zero':
                    self.wipe_return_code = self.zero_device(self.wipe_device,self.diskslaw_configuration.mech_wipe_rounds)
                    self.wipe_type += "zero"
                else:
                    self.wipe_return_code = self.shred_device(self.wipe_device,self.diskslaw_configuration.mech_wipe_rounds)
                    self.wipe_type += "shred"
            else:
                #Get time elapsed
                elapsed = monotonic()-self.wipe_start
                #If we are far off from estimated time, sleep to allow the drive to finish up
                if(((estimated_time*60)) > (elapsed)):
                    if(elapsed < 10):
                        #We probably didn't even try to secure erase
                        sleep(1)
                    else:
                        sleep(int((estimated_time*60)-elapsed))
                self.wipe_return_code = se_ret
                self.wipe_type += "secure erase"
        self.end_wipe()