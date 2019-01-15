from subprocess import call
from diskslaw_block import get_rotational,get_secure_erase,get_drive_has_master_password,get_secure_erase_time
from time import sleep,monotonic
import threading

class disk_eraser(threading.Thread):
    wipe_return_code=-1
    wipe_type=""
    wipe_device = ""

    mech_wipe_type = "zero"
    mech_wipe_rounds = 1

    def __init__(self,device,mechanical_wipe_type="zero",mechanical_rounds=1):
        threading.Thread.__init__(self)
        self.mech_wipe_rounds = mechanical_rounds
        self.mech_wipe_type = mechanical_wipe_type
        self.wipe_device = device
    def run(self):
        self.wipe(self.wipe_device,self.mech_wipe_type,self.mech_wipe_rounds)
    def nvme_wipe(self,device,wipe_type=1):
        retcode = call(['nvme','format',('/dev/'+device),'-s',wipe_type])
        return (retcode == 0)

    def sata_secure_erase(self,device,password,user='u',expected_time=0):
        retcode = call(['hdparm','--user-master',user,'--security-erase',password,('/dev/'+device)])
        return (retcode == 0)

    def sata_set_password(self,device,password,user='u'):
        retcode = call(['hdparm','--user-master',user,'--security-set-pass',password,('/dev/'+device)])
        return (retcode == 0)

    def sata_disable_password(self,device,password):
        retcode = call(['hdparm','--security-disable',password,('/dev/'+device)])
        return (retcode == 0)

    def shred_device(self,device,rounds=1):
        retcode = call(['shred',('-n '+rounds),'--verbose',('/dev/'+device)])
        return (retcode == 0)

    def zero_device(self,device,rounds=1):
        retcode = 0
        for _ in range(rounds):
            retcode += call(['dd','if=/dev/zero',('of=/dev/'+device),'bs=1M'])
        return (retcode == 0)

    def wipe(self,device,mechanical_wipe_type='zero',mechanical_rounds=1):
        if 'nvme' in device:
            #NVMe drive, wipe
            self.wipe_return_code = self.nvme_wipe(device)
            self.wipe_type = "nvme format"
        elif get_secure_erase(device) == True:
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
            #Wipe
            se_ret = self.sata_secure_erase(device,'pass')
            #Get time elapsed
            elapsed = monotonic()-start_time
            #If we are far off from estimated time, sleep to allow the drive to finish up
            if(((estimated_time*60)*0.9) > (elapsed)):
                sleep(int((estimated_time*60)-elapsed))
            #Disable the password so we don't lock the drive access
            self.sata_disable_password(device,'pass')
            self.wipe_return_code = se_ret
            self.wipe_type = "secure erase"
        else:
            #Mechanical Drive probably, doesn't support secure erase so write to it
            if mechanical_wipe_type == 'zero':
                self.wipe_return_code = self.zero_device(device,mechanical_rounds)
                self.wipe_type = "zero"
            else:
                self.wipe_return_code = self.shred_device(device,mechanical_rounds)
                self.wipe_type = "shred"