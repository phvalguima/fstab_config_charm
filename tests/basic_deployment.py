#!/usr/bin/python3
"""
Ubuntu charm functional test using Zaza. Take note that the Ubuntu
charm does not have any relations or config options to exercise.
"""

import unittest
import time
import zaza.model as model


CONFIGMAP_DEFAULT="""- filesystem: {}:/srv/test
  mountpoint: /srv/test
  type: nfs
  options: rw,nosuid
"""

MODEL_DEFAULT_NAME = 'default'

class BasicDeployment(unittest.TestCase):
    
    def test_001_nfs_integration(self):

        import pdb
        pdb.set_trace()
        nfs = model.get_units('ubuntu')[0]
        fstab = model.get_units('fstab-config')[0]

        while fstab.agent_status() != 'active' or \
              nfs.agent_status() != 'active':
            print("Status for charms are: {} {}".
                  format(fstab.agent_status(),
                         nfs.agent_status()))
            time.sleep(300)
        
        model.run_on_leader('ubuntu', 'sudo mkdir /srv/nfs')
        model.run_on_leader('ubuntu', 'echo "/srv/nfs *(rw,sync,no_subtree_check)" | sudo tee /etc/exports')
        model.run_on_leader('ubuntu', 'sudo chown nobody:nogroup /srv/nfs')
        model.run_on_leader('ubuntu', 'sudo chmod 777 /srv/nfs')
        model.run_on_leader('ubuntu', 'sudo exportfs -r')

        time.sleep(180)

        fstab_config = CONFIGMAP_DEFAULT.format(nfs.public_address())
        print("Testing on following option:\n{}".format(fstab_config))
        model.get_application('fstab_config').set_config({'configmap': fstab_config})

        time.sleep(120)
        while fstab.agent_status() != 'active' or \
              nfs.agent_status() != 'active':
            print("Status for charms are: {} {}".
                  format(fstab.agent_status(),
                         nfs.agent_status()))
            time.sleep(180)
        
