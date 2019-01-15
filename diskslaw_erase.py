from subprocess import call
from diskslaw_block import get_rotational,get_secure_erase

def nvme_wipe(device,wipe_type=1):
    retcode = call(['nvme','format',('/dev/'+device),'-s',wipe_type])
    return (retcode == 0)

def sata_secure_erase(device,password,user='u',expected_time=0):
    retcode = call(['hdparm','--user-master',user,'--security-erase',password,('/dev/'+device)])
    return (retcode == 0)

def sata_set_password(device,password,user='u'):
    retcode = call(['hdparm','--user-master',user,'--security-set-pass',password,('/dev/'+device)])
    return (retcode == 0)

def sata_disable_password(device,password):
    retcode = call(['hdparm','--security-disable',password,('/dev/'+device)])
    return (retcode == 0)

def shred_device(device,rounds=1):
    retcode = call(['shred',('-n '+rounds),'--verbose',('/dev/'+device)])
    return (retcode == 0)

def zero_device(device,rounds=1):
    retcode = 0
    for i in range(rounds):
        retcode += call(['dd','if=/dev/zero',('of=/dev/'+device),'bs=1M'])
    return (retcode == 0)

def wipe(device,mechanical_wipe_type='zero',mechanical_rounds=1):
    print("Not Defined")