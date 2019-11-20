import os
import yaml
import subprocess

from charms.reactive import when, when_not, set_flag
from charms.layer import fstab_parser
from charms.apt import queue_install
from charmhelpers.core import hookenv, unitdata


def get_last_modification_fstab():
    stat = os.path.getmtime('/etc/fstab')
    return '{}'.format(round(stat))


@when_not('fstab_config.installed')
def install_fstab_config():
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    queue_install(['nfs-common',
                   'cifs-utils'])
    hookenv.status_set('maintenance','waiting for installation')


@when('apt.installed.nfs-common')
@when('apt.installed.cifs-utils')
def set_installed_message():
    set_flag('fstab_config.installed')    
    hookenv.status_set('active','packages have been installed')


def is_equal_list_dicts(a, b):
    if len(a) != len(b):
        return False

    for elem in a:
        for el_b in b:
            for i in elem:
                if not i in el_b:
                    return False
                if elem[i] != el_b[i]:
                    return False
    return True
            

@when('config.changed.configmap')
@when('fstab_config.installed')
def config_changed():
    db = unitdata.kv()
    old_configmap = yaml.load(db.get('previous_configmap'))
    fstab_entries = hookenv.config('configmap')    
    hookenv.status_set('maintenance','[config-changed] updating fstab following configmap...')
    configmap = yaml.load(fstab_entries)

    if configmap == None or len(configmap) == 0:
        configmap = list()
    if old_configmap == None or len(old_configmap) == 0:
        old_configmap = list()

    if is_equal_list_dicts(configmap, old_configmap):
        # configmap is the same, we return
        hookenv.log('Configmap entered {} and old value {} are the same'
                    .format(fstab_entries, old_configmap),
                    hookenv.DEBUG)
        hookenv.log('Same configmap supplied as already-installed '
                    'configuration, ignoring...',
                    hookenv.INFO)
        return
        
    fstab_parser.dict_to_fstab(configmap,
                               old_configmap,
                               hookenv.config('enforce-config'),                               
                               hookenv.config('mount-timeout'))
    
    now = get_last_modification_fstab()
    db.set('fstab_last_update', now)
    db.flush()
    db.set('previous_configmap', hookenv.config('configmap'))
    db.flush()
    hookenv.status_set('active','fstab is configured')


@when('update.status')
def update_status():
    recent_mod = get_last_modification_fstab()
    last_mod = unitdata.kv().get('stab_last_update')
    if recent_mod > last_mod:
        config_changed()
    try:
        subprocess.check_output(['mount', '-a'], timeout=hookenv.config('mount-timeout'))
    except subprocess.TimeoutExpired:
        hookenv.status_set('blocked','Timed out on mount. Please, check configmap')
        
