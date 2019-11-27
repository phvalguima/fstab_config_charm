import sys
import mock
import types

sys.path.append('src')
sys.path.append('src/lib')

apt = mock.MagicMock()

sys.modules['charms.apt'] = apt
