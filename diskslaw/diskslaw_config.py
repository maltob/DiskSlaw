class diskslaw_config:
    #Parameters
    mech_wipe_type = "zero"
    mech_wipe_rounds = 1
    nvme_wipe_type = 1
    always_shred = False
    attempt_enhanced_secure_erase = False
    always_shred_rotational = False
    validation_text = "HECTORSPECTORSELECTOR"

    #Lookup for NVM wipe
    nvme_wipe_lookup = ('None','Data','Cryptographic')

    def __init__(self,mechanical_wipe_type="zero",mechanical_rounds=1,nvme_wipe_type=1,always_shred=False,attempt_enhanced_secure_erase=False,always_shred_rotational=False,validation_text="HECTORSPECTORSELECTOR"):
        self.mech_wipe_rounds = mechanical_rounds
        self.mech_wipe_type = mechanical_wipe_type
        self.nvme_wipe_type = nvme_wipe_type
        self.always_shred = always_shred
        self.attempt_enhanced_secure_erase = attempt_enhanced_secure_erase
        self.always_shred_rotational = always_shred_rotational
        self.validation_text = validation_text

    def load_from_hash(self,hash_table):
        if 'shred_method' in hash_table:
            if hash_table['shred_method'] == 'zero':
                self.mech_wipe_type = 'zero'
            else:
                self.mech_wipe_type = 'random'
        if 'shred_rounds' in hash_table:
            try:
                if int(hash_table['shred_rounds'] ) > 1:
                    self.mech_wipe_rounds = int(hash_table['shred_rounds'])
            except:
                print("ERROR reading shred rounds")
        if 'attempt_enhanced_secure_erase' in hash_table:
            self.attempt_enhanced_secure_erase = bool(hash_table['attempt_enhanced_secure_erase'])
        if 'always_shred' in hash_table:
            self.always_shred = bool(hash_table['always_shred'])
        if 'always_shred_rotational' in hash_table:
            self.always_shred_rotational = bool(hash_table['always_shred_rotational'])
        # There's only two actually valid wipe types for NVMe, 1 and 2
        if 'nvme_wipe_type' in hash_table:
            try:
                if int(hash_table['nvme_wipe_type'] ) > 0 and int(hash_table['nvme_wipe_type'] ) < 3:
                    self.nvme_wipe_type = int(hash_table['nvme_wipe_type'])
            except:
                print("ERROR reading nvme_wipe_type")
        