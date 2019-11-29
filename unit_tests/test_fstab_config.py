from mock import (
    patch,
    Mock,
    mock_open,
    call,
)
import yaml
import unittest
from reactive.fstab_config import (
    config_changed
)

from charmhelpers.core import hookenv



RAW_FSTAB = """# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>

UUID=aaa-bbb / ext4 errors=remount-ro    0       1
nfs:/testingand /test/and nfs rsize=10 and wsize=20,option 0 2
"""

TEST_001_EXPECTED_RESULT_FSTAB = """# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>


nfs:/testingand /test/and nfs rsize=10,wsize=20,option 0 2

UUID=aaa-bbb / ext4 errors=remount-ro    0       1

nfs:/shares /test/var nfs rsize=10,wsize=8192 0 2
"""

TEST_002_EXPECTED_RESULT_FSTAB = """# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>


nfs:/testingand /test/and nfs rsize=10,wsize=20,option 0 2
"""

TEST_001_NEW_CONFIG = """- filesystem: UUID=aaa-bbb
  mountpoint: /
  type: ext4
  options: testing
  dump: 0
  pass: 1
- filesystem: nfs:/shares
  mountpoint: /test/var
  type: nfs
  options: 'rsize=10,wsize=8192'
  dump: 0
  pass: 2
"""

TEST_003_WRONG_CONFIG = """- filesystem: UUID=ccc-ccc
  mountpoint: /
  type: blabla
  options: testing
  dump: 0
  pass: 1
"""


class TestCharm(unittest.TestCase):

    @patch('subprocess.check_output',
           Mock(return_value=""))
    @patch('charmhelpers.core.unitdata.kv')
    @patch('charmhelpers.core.hookenv.config')
#    @patch('jinja2.loaders.open_if_exists')
    @patch('lib.charms.layer.fstab_parser.Environment.get_template')
    @patch('charmhelpers.core.hookenv.status_set',
           Mock(return_value=""))
    @patch('os.listdir',
           Mock(return_value=""))
    def test_001_config_changed_call(self,
#                                     mock_if_exists,
                                     mock_env,
                                     mock_hookenv_config,
                                     mock_kv):

        def mock_config_options(config):
            if config == 'configmap':
                return TEST_001_NEW_CONFIG
            elif config == 'mount-timeout':
                return 20
            elif config == 'enforce-config':
                return False
#        class open_if_exists_mock(object):
#            @staticmethod
#            def read():
#                template = None
#                with open("./templates/fstab.templates") as f:
#                    template = "".join(f.readlines())
#                    f.close()
#                return template.encode('utf-8')
#            @staticmethod
#            def close():
#                return
        mock_hookenv_config.side_effect = mock_config_options
        mock_kv.return_value.get.return_value = ''
        mock_kv.return_value.set.return_value = Mock()
        mock_kv.return_value.flush.return_value = Mock()
        m = mock_open(read_data=RAW_FSTAB)
#        mock_if_exists.return_value = open_if_exists_mock
        def mock_template(render_mock):
            return Mock(return_value=render_mock)
        render_mock = Mock()
        mock_env.return_value = mock_template(render_mock)
        with patch('builtins.open', m):
            import pdb
            pdb.set_trace()
            config_changed()
        m().write.assert_called_once_with(
            TEST_001_EXPECTED_RESULT_FSTAB
        )

    @patch('subprocess.check_output',
           Mock(return_value=""))
    @patch('charmhelpers.core.unitdata.kv')
    @patch('charmhelpers.core.hookenv.config')
    @patch('charmhelpers.core.hookenv.status_set',
           Mock(return_value=""))
    def test_002_config_changed_to_empty_value(self,
                                               mock_hookenv_config,
                                               mock_kv):

        def mock_config_options(config):
            if config == 'configmap':
                return ''
            elif config == 'mount-timeout':
                return 20
            elif config == 'enforce-config':
                return False
        mock_hookenv_config.side_effect = mock_config_options
        # Recover old config from TEST_001...
        mock_kv.return_value.get.return_value = TEST_001_NEW_CONFIG
        mock_kv.return_value.set.return_value = Mock()
        mock_kv.return_value.flush.return_value = Mock()
        m = mock_open(read_data=TEST_001_EXPECTED_RESULT_FSTAB)
        with patch('builtins.open', m):
            config_changed()
        m().write.assert_called_once_with(
            TEST_002_EXPECTED_RESULT_FSTAB
        )

    @patch('subprocess.check_output',
           Mock(return_value=""))
    @patch('charmhelpers.core.unitdata.kv')
    @patch('charmhelpers.core.hookenv.config')
    @patch('charmhelpers.core.hookenv.log')
    @patch('charmhelpers.core.hookenv.status_set',
           Mock(return_value=""))
    @patch('os.listdir',
           Mock(return_value=""))
    def test_003_force_fail_check_configmap(self,
                                            mock_log,
                                            mock_hookenv_config,
                                            mock_kv):

        def mock_config_options(config):
            if config == 'configmap':
                return TEST_003_WRONG_CONFIG
            elif config == 'mount-timeout':
                return 20
            elif config == 'enforce-config':
                return False
        mock_hookenv_config.side_effect = mock_config_options
        # Recover old config from TEST_001...
        mock_kv.return_value.get.return_value = TEST_001_NEW_CONFIG
        mock_kv.return_value.set.return_value = Mock()
        mock_kv.return_value.flush.return_value = Mock()
        m = mock_open(read_data=TEST_001_EXPECTED_RESULT_FSTAB)
        with patch('builtins.open', m):
            config_changed()
        calls = [call("Old Configmap recovered from DB is: [{'filesystem': 'UUID=aaa-bbb', 'mountpoint': '/', 'type': 'ext4', 'options': 'testing', 'dump': 0, 'pass': 1}, {'filesystem': 'nfs:/shares', 'mountpoint': '/test/var', 'type': 'nfs', 'options': 'rsize=10,wsize=8192', 'dump': 0, 'pass': 2}]"), call('(config_changed.check_configmap) Unrecognized FS type: blabla for filesystem: UUID=ccc-ccc', 'WARNING')]  # noqa
        mock_log.assert_has_calls(calls, any_order=True)
