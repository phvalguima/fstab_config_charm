from mock import (
    patch,
    Mock,
    mock_open,
)
import yaml
import unittest
from reactive.fstab_config import (
    config_changed
)


RAW_FSTAB="""# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>

UUID=aaa-bbb / ext4 errors=remount-ro    0       1
nfs:/testingand /test/and nfs rsize=10 and wsize=20,option 0 2
"""

EXPECTED_RESULT_FSTAB="""# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>


nfs:/testingand /test/and nfs rsize=10,wsize=20,option 0 2

UUID=aaa-bbb / ext4 testing 0 1

nfs:/shares /test/var nfs rsize=10 and wsize=8192 0 2
"""


NEW_CONFIG="""- filesystem: UUID=aaa-bbb
  mountpoint: /
  type: ext4
  options: testing
  dump: 0
  pass: 1
- filesystem: nfs:/shares
  mountpoint: /test/var
  type: nfs
  options: ''
  rsize: 10
  wsize: 8192
  dump: 0
  pass: 2  
"""

class TestCharm(unittest.TestCase):

    @staticmethod
    def mock_config_options(config):
        if config == 'configmap':
            return NEW_CONFIG
        elif config == 'enforce-config':
            return False

    @patch('subprocess.check_output',
           Mock(return_value=""))
    @patch('charmhelpers.core.unitdata.kv')
    @patch('charmhelpers.core.hookenv.config')
    @patch('charmhelpers.core.hookenv.status_set',
           Mock(return_value=""))
    def test_config_changed(self,
                            mock_hookenv_config,
                            mock_kv):

        mock_hookenv_config.side_effect = self.mock_config_options
        mock_kv.return_value.set.return_value = Mock()
        mock_kv.return_value.flush.return_value = Mock()
        m = mock_open(read_data = RAW_FSTAB)
        with patch('charms.layer.fstab_parser.open', m):
            config_changed()
        m().write.assert_called_once_with(
            EXPECTED_RESULT_FSTAB
        )
