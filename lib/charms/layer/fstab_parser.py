import re
import os
import subprocess
import yaml
from jinja2 import Environment, BaseLoader

fstab_template = """# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>

{% for fs in fstab %}
{{ fs['filesystem'] }} {{ fs['mountpoint'] }} {{ fs['type'] }} {{ fs['options'] }} {{ fs['dump'] }} {{ fs['pass'] }}
{% endfor %}
"""

EXPECTED_FS_TYPES=["xt2", "ext3", "ext4", "xfs", "btrfs", "vfat", "sysfs", "proc", "nfs", "cifs", "none"]


class ConfigmapMissingException(Exception):

    ##
    # Code values:
    # 0 - filesystem key on configmap item missing
    # 1 - mountpoint key on configmap item missing
    # 2 - type key on configmap item missing
    # 3 - Unknown failure when mountpoint mkdir -p was ran
    # 4 - mountpoint folder is not empty
    # 5 - NFS target unreachable
    def __init__(self, message, errorcode):
        super(ConfigmapMissingException, self).__init__(message)
        self.errorcode = errorcode


# Returns None if everything went OK
# Returns message to WARN logs otherwise
def check_configmap(configmap):
    # If missing any of obligatory fields:
    result = ""
    for e in configmap:
        if "filesystem" not in e:
            raise ConfigmapMissingException("Missing filesystem entry", 0)
        if "mountpoint" not in e:
            raise ConfigmapMissingException(
                "Missing mountpoint entry on filesystem {}"
                .format(e["filesystem"]), 1)
        if "type" not in e:
            raise ConfigmapMissingException(
                "Missing type entry on filesystem {}"
                .format(e["type"]), 2)
        if e['type'] is None:
            e['type'] = ""
        # Do not block or raise anything here since list is not exhaustive
        if e['type'] not in EXPECTED_FS_TYPES:
            result = result + \
                     "Unrecognized FS type: {} for filesystem: {}" \
                     .format(e["type"],
                             e["filesystem"])
        # Ensure all folders are created beforehand
        try:
            subprocess.check_output(['mkdir', '-p', e['mountpoint']])
        except subprocess.CalledProcessError as e:
            raise ConfigmapMissingException(
                "Mountpoint {} for filesystem {} failed mkdir -p"
                .format(e["mountpoint"],
                        e["filesystem"]), 3)
        if len(os.listdir(e["mountpoint"])) != 0:
            # Folder has content
            raise ConfigmapMissingException(
                "Mountpoint {} for filesystem {} is not empty"
                .format(e["mountpoint"],
                        e["filesystem"]), 4)
        if e["type"] == "nfs":
            try:
                subprocess.check_output(['showmount',
                                         '-e',
                                         '{}'
                                         .format(e['filesystem']
                                                 .split(':')[0])])
            except subprocess.CalledProcessError as e:
                raise ConfigmapMissingException(
                    "Mountpoint {} for filesystem {} "
                    "NFS target is unreachable"
                    .format(e["mountpoint"],
                            e["filesystem"]), 5)
    if result == "":
        return None
    return result


# Remove any entry from target present on both configmaps
def remove_redundancies(target_configmap,
                        other_cm):

    if other_cm is not None and \
       len(other_cm) > 0:
        for n in other_cm:
            for fs in target_configmap:
                if n['filesystem'] == fs['filesystem']:
                    target_configmap.remove(fs)
                    break
    return target_configmap


def dict_to_fstab(fs_configmap, old_configmap=None,
                  enforce=False, timeout=300):

    fstab = ''

    with open('/etc/fstab', 'r') as f:
        fstab = fstab_to_dict(f.readlines())
        f.close()

    if not enforce:        
        remove_redundancies(
            target_configmap=fstab, other_cm=fs_configmap)
        remove_redundancies(
            target_configmap=fstab, other_cm=old_configmap)
        for fs in fs_configmap:
            fstab.append(fs)
    else:
        fstab = fs_configmap

    templ = Environment(loader=BaseLoader()).from_string(fstab_template)
    fstab_content = templ.render(fstab=fstab)
    return fstab_content


def fstab_to_dict(fstab):
    result = []
    # Remove any lines starting with comment flag
    # clean comments from lines
    fs = [re.sub(r'\#.*$', '', i) for i in fstab if not i.startswith('#')]
    # and, remove the newline if present
    fs = [re.sub(r'(\r\n|\r|\n)', '', i)
          for i in fs if len(re.sub(r'(\r\n|\r|\n)', '', i)) > 0]
    for i in fs:  # Now we process line by line
        attrs = re.split(' |\t', i)
        # As per: https://help.ubuntu.com/community/Fstab
        # we need to account for a case where we have:
        # Server:/share  /media/nfs  nfs
        #      rsize=8192 and wsize=8192,noexec,nosuid
        # that will break into 'rsize=8192','and','wsize=8192,noexec,nosuid'
        for j in attrs:
            if j == 'and':
                index = attrs.index(j)
                attrs[index-1] = '{},{}'.format(attrs[index-1],
                                                attrs[index+1])
                # Merged whatever existed between and
                # Now clean up since it is all in the same string
                attrs.remove(attrs[index+1])
                attrs.remove(attrs[index])
        entry = {
            'filesystem': attrs[0],
            'mountpoint': attrs[1],
            'type': attrs[2]
        }
        if len(attrs) >= 4:
            entry['options'] = attrs[3]
        if len(attrs) >= 5:
            entry['dump'] = attrs[4]
        if len(attrs) >= 6:
            entry['pass'] = attrs[5]
        result.append(entry)
    if len(result) == 0:
        return None
    return result
