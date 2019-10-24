import os
import yaml

from charms.reactive import when, when_not, set_flag
from charms.layer import fstab_parser
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
    set_flag('fstab_config.installed')


@when('config.changed.configmap')
def config_changed():
    fstab_entries = hookenv.config('configmap')
    # Do nothing configmap is empty
    if fstab_entries == None or len(fstab_entries) == 0:
        return
    hookenv.status_set('maintenance','[config-changed] updating fstab following configmap...')
    configmap = yaml.load(fstab_entries)
    fstab_parser.dict_to_fstab(configmap, hookenv.config('enforce-config'))
    now = get_last_modification_fstab()
    db = unitdata.kv()
    db.set('fstab_last_update', now)
    db.flush()
    hookenv.status_set('active','fstab is configured')


@when('update.status')
def update_status():
    recent_mod = get_last_modification_fstab()
    last_mod = unitdata.kv().get('stab_last_update')
    if recent_mod > last_mod:
        config_changed()
