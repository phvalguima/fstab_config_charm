#!/usr/bin/python3
"""
Ubuntu charm functional test using Zaza. Take note that the Ubuntu
charm does not have any relations or config options to exercise.
"""

import unittest
import time
import zaza.model as model


CONFIGMAP_DEFAULT="""- filesystem: {}:/srv/data
  mountpoint: /test/nfs1
  type: nfs
  options: errors=remount,ro
  dump: 1
  pass: 2
- filesystem: {}:/srv/data
  mountpoint: /test2/nfs2
  type: nfs
  options: errors=remount,ro
  dump: 1
  pass: 2
"""

MODEL_DEFAULT_NAME = 'default'

class BasicDeployment(unittest.TestCase):
    
    def test_set_2_nfs_and_touch_file(self):
        model_name = model.async_get_juju_model()
        print("Model name is {}".format(model_name))
        first_unit_nfs1 = model.get_units('nfs1')[0]
        first_unit_nfs2 = model.get_units('nfs2')[0]
        while model.check_unit_workload_status(MODEL_NAME,first_unit_nfs1,'active') or \
              model.check_unit_workload_status(MODEL_NAME,first_unit_nfs2,'active'):
            print("Unit {} still not active".format(first_unit_nfs1))
            print("Unit {} still not active".format(first_unit_nfs2))
            time.sleep(180)
        
        ip_nfs1 = model.get_app_ips('nfs1')[0]
        ip_nfs2 = model.get_app_ips('nfs2')[0]
        print("NFS IPs found are: {} and {}".format(ip_nfs1, ip_nfs2))
        configmap = CONFIGMAP_DEFAULT.format(ip_nfs1, ip_nfs2)
        
        model.async_set_application_config(model_name,'fstab-config',configmap)
        time.sleep(300) # Wait five minutes and check for unit status        
        first_unit = model.get_units('fstab-config')[0]
        state = None        
        while not state = model.check_unit_workload_status(MODEL_NAME,first_unit,'active'):
            print("Unit {} still on {} state".format(first_unit, state))
            time.sleep(180)

        result1 = model.run_on_leader('fstab-config','sudo mkdir /test/nfs1/test')
        self.assertEqual(result1['Code'], '0')
        result2 = model.run_on_leader('fstab-config','sudo mkdir /test2/nfs2/test')
        self.assertEqual(result2['Code'], '0')
        
