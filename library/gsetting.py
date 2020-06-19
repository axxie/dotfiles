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


class Gsetting(object):

    def __init__(self, module, check_mode=False):
        self.module = module
        self.check_mode = check_mode

    def _get(self, path, key):

        rc, out, err = self.module.run_command(["gsettings", "get", path, key])
        if rc != 0:
            self.module.fail_json(msg='gsettings failed while getting the value with error: %s' % err)

        return out.strip('\n')

    def _set(self, path, key, value):
        # Run the command and fetch standard return code, stdout, and stderr.
        dbus_wrapper = DBusWrapper(self.module)
        rc, out, err = dbus_wrapper.run_command(["gsettings", "set", path, key, value])
        if rc != 0:
            self.module.fail_json(msg='gsettings failed while setting the value with error: %s' % err)

    def set(self, path, key, value):

        current_value = self._get(path, key)

        if current_value == value:
            return False
        elif self.check_mode:
            return True

        self._set(path, key, value)

        # Value was changed.
        return True


def main():
    # Setup the Ansible module
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='str'),
            key=dict(required=True, type='str'),
            value=dict(required=True, type='str'),
        ),
        supports_check_mode=True
    )

    # Create wrapper instance.
    setting = Gsetting(module, module.check_mode)

    changed = setting.set(module.params['path'], module.params['key'], module.params['value'])
    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
