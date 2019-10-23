#!/usr/bin/python3
"""
Ubuntu charm functional test using Zaza. Take note that the Ubuntu
charm does not have any relations or config options to exercise.
"""

import unittest
import time
import zaza.model as model


CONFIGMAP_DEFAULT="""- filesystem: 
"""

class BasicDeployment(unittest.TestCase):
    
    def test_set_2_nfs_and_touch_file(self):        
        model.async_set_application_config('default','fstab-config',configmap)
        time.sleep(300) # Wait five minutes and check for unit status
        first_unit = model.get_units('fstab-config')[0]
        state = None
        while not state = model.check_unit_workload_status(MODEL_NAME,first_unit,'active'):
            print("Unit {} still on {} state".format(first_unit, state))
            time.sleep(180)
