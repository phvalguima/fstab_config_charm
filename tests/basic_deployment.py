#!/usr/bin/python3
"""
Ubuntu charm functional test using Zaza. Take note that the Ubuntu
charm does not have any relations or config options to exercise.
"""

import unittest
import time
import zaza.model as model
import zaza.utilities.generic as series_upgrade_application
import asyncio


CONFIGMAP_TEST_001 = """- filesystem: {}:/srv/nfs
  mountpoint: /srv/test
  type: nfs
  options: rw,nosuid
"""

CONFIGMAP_TEST_002 = CONFIGMAP_TEST_001 + """- filesystem: /srv/test
  mountpoint: /srv/testbind
  type: none
  options: bind
"""

MODEL_DEFAULT_NAME = 'default'


class BasicDeployment(unittest.TestCase):

    nfs_public_address = ""

    def test_001_nfs_integration(self):

        nfs = model.get_unit_from_name('ubuntu/0')
        fstab = model.get_unit_from_name('fstab-config/0')

        model.run_on_leader('ubuntu', 'export DEBIAN_FRONTEND=noninteractive;'
                            ' sudo apt -y install nfs-common '
                            'nfs-kernel-server')
        model.run_on_leader('ubuntu', 'sudo mkdir /srv/nfs')
        model.run_on_leader('ubuntu', 'echo "/srv/nfs '
                            '*(rw,sync,no_subtree_check)" '
                            '| sudo tee /etc/exports')
        model.run_on_leader('ubuntu', 'sudo chown nobody:nogroup /srv/nfs')
        model.run_on_leader('ubuntu', 'sudo chmod 777 /srv/nfs')
        model.run_on_leader('ubuntu', 'sudo exportfs -r')

        self.nfs_public_address = nfs.public_address
        fstab_config = CONFIGMAP_TEST_001.format(self.nfs_public_address)
        print("Testing on following option:\n{}".format(fstab_config))

        async def await_app_config(name, config):
            return(await model.async_set_application_config(name, config))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fstab_app = loop.run_until_complete(
            await_app_config('fstab-config',
                             {
                                 'configmap': fstab_config
                             }))

        result = model.run_on_leader('fstab-config',
                                     'sudo touch /srv/test/test001')
        self.assertEqual(result['Code'], '0')

    def test_002_nfs_bind(self):

        nfs = model.get_unit_from_name('ubuntu/0')
        fstab_config = CONFIGMAP_TEST_002.format(nfs.public_address)
        print("Testing on following option:\n{}".format(fstab_config))
        async def await_app_config(name, config):
            return(await model.async_set_application_config(name, config))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fstab_app = loop.run_until_complete(
            await_app_config('fstab-config',
                             {'configmap': fstab_config}))
        result = model.run_on_leader('fstab-config',
                                     'sudo touch /srv/testbind/test002')
        self.assertEqual(result['Code'], '0')

    def test_003_bionic_to_disco_upgrade(self):

        series_upgrade_application('fstab-config',
                                   pause_non_leader_primary=False,
                                   from_series="bionic",
                                   to_series="disco")
        result = model.run_on_leader('fstab-config',
                                     'sudo touch /srv/testbind/test003')
        self.assertEqual(result['Code'], '0')
