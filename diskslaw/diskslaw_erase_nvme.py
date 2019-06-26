import diskslaw_erase
from subprocess import call,Popen,PIPE,DEVNULL

class disk_eraser_nvme(diskslaw_erase.disk_eraser):
    def __init__(self,device,config):
        super().__init__(device,config)

    def nvme_wipe(self,device,wipe_type=1):
        retcode = call(['nvme','format',('/dev/'+device),'-s',str(wipe_type)],None,stdout=open('/tmp/diskslaw_nvme_'+device+'.log','w'),stderr=open('/tmp/diskslaw_nvme_err_'+device+'.log','w'))
        return retcode

    def get_wipe_progress(self):
        #No progress indicator for NVMe wipe
        return ''

    def wipe(self):
        wipe_started = self.init_wipe()
        if wipe_started == True:
            #NVMe drive, wipe
            self.wipe_type = ""
            nvme_ret = self.nvme_wipe(self.wipe_device,self.diskslaw_configuration.nvme_wipe_type)
            if nvme_ret == 0:
                nvme_se_text = self.diskslaw_configuration.nvme_wipe_lookup[self.diskslaw_configuration.nvme_wipe_type]
                self.wipe_type = "nvme "+nvme_se_text+" wipe"
                self.wipe_return_code = nvme_ret

            if nvme_ret != 0 or self.diskslaw_configuration.always_shred == True:
                #Fall back to shred
                if self.diskslaw_configuration.always_shred == True and self.wipe_type != "":
                    self.wipe_type += " + "
                if self.diskslaw_configuration.mech_wipe_type == 'zero':
                    self.wipe_return_code = self.zero_device(self.wipe_device,self.diskslaw_configuration.mech_wipe_rounds)
                    self.wipe_type += "zero"
                else:
                    self.wipe_return_code = self.shred_device(self.wipe_device,self.diskslaw_configuration.mech_wipe_rounds)
                    self.wipe_type += "shred"
        self.end_wipe()