#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, print_function

__metaclass__ = type

# Based on standard dconf module.
# Adds or removes the application to/from Gnome favorites (dock).

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.module_utils.dbuswrapper import DBusWrapper
except ImportError:
    # For debugging module locally
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'module_utils'))
    from dbuswrapper import DBusWrapper

FAVORITES_ARGS = ["org.gnome.shell", "favorite-apps"]


class FavoritesPreference(object):

    def __init__(self, module, check_mode=False):
        self.module = module
        self.check_mode = check_mode

    def _get(self):

        command = ["gsettings", "get"] + FAVORITES_ARGS
        rc, out, err = self.module.run_command(command)
        if rc != 0:
            self.module.fail_json(msg='gsettings failed while getting the value with error: %s' % err)

        return list(map(lambda x: x.strip(" \'\""), out.strip('[]\n').split(',')))

    def _set(self, favorites):
        favorites_string = "[" + ",".join(map(lambda x: "'" + x + "'", favorites)) + "]"
        command = ["gsettings", "set"] + FAVORITES_ARGS + [ favorites_string ]

        # Run the command and fetch standard return code, stdout, and stderr.
        dbus_wrapper = DBusWrapper(self.module)
        rc, out, err = dbus_wrapper.run_command(command)
        if rc != 0:
            self.module.fail_json(msg='gsettings failed while setting the value with error: %s' % err)

    def update(self, callback):

        favorites = self._get()
        # new_favorites = favorites[:] # copy favorites
        # callback(new_favorites) # mutate copied version

        new_favorites = callback(favorites)

        if new_favorites == favorites:
            return False
        elif self.check_mode:
            return True

        self._set(new_favorites)

        # Value was changed.
        return True


def main():
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            app=dict(required=True, type='str'),
        ),
        supports_check_mode=True
    )

    # Create wrapper instance.
    preference = FavoritesPreference(module, module.check_mode)

    # Process based on different states.
    app = module.params['app']
    if module.params['state'] == 'present':
        changed = preference.update(lambda favorites: favorites if app in favorites else favorites + [app])
        module.exit_json(changed=changed)
    elif module.params['state'] == 'absent':
        changed = preference.update(lambda favorites: [x for x in favorites if x != app])
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
