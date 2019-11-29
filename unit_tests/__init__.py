import sys
import mock
import types

sys.path.append('src')
sys.path.append('src/lib')

apt = mock.MagicMock()

sys.modules['charms.apt'] = apt
#sys.modules['jinja2.FileSystemLoader'] = mock.MagicMock()
#sys.modules['jinja2.FileSystemLoader.Environment'] = mock.MagicMock()
#sys.modules['jinja2.FileSystemLoader.Environment.get_template'] = mock.MagicMock()
#template = None
#with open("./templates/fstab.j2") as f:
#    template = "".join(f.readlines())
#    f.close()
#sys.modules['jinja2.FileSystemLoader.Environment.get_template.render'] = mock.MagicMock(return_value=template)

