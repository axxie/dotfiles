#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, print_function
import subprocess

__metaclass__ = type

# Based on standard dconf module.
# Adds or removes the application to/from Gnome favorites (dock).


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

import os
import traceback

PSUTIL_IMP_ERR = None
try:
    import psutil

    psutil_found = True
except ImportError:
    PSUTIL_IMP_ERR = traceback.format_exc()
    psutil_found = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class DBusWrapper(object):

    def __init__(self, module):
        # Store passed-in arguments and set-up some defaults.
        self.module = module

        # Try to extract existing D-Bus session address.
        self.dbus_session_bus_address = self._get_existing_dbus_session()

        # If no existing D-Bus session was detected, check if dbus-run-session
        # is available.
        if self.dbus_session_bus_address is None:
            self.module.get_bin_path('dbus-run-session', required=True)

    def _check_output_strip(self, command):
        return subprocess.check_output(command).decode('utf-8').strip()
    
    def _get_gnome_version(self):
        return tuple(map(int, (self._check_output_strip(
            ['gnome-shell', '--version']).split(' ')[2].split('.'))))

    def _get_dbus_bus_address_no_psutil(self, uid):
        user = str(uid)
        pgrep_cmd = ['pgrep', '-u', user, 'gnome-session']
        gnome_ver = self._get_gnome_version()
        if (gnome_ver >= (3, 33, 90)):
            # From GNOME 3.33.90 session process has changed
            # https://github.com/GNOME/gnome-session/releases/tag/3.33.90
            pgrep_cmd = ['pgrep', '-u', user, '-f', 'session=gnome']

        try:
            pid = self._check_output_strip(pgrep_cmd)
        except subprocess.CalledProcessError:
           return None

        if pid:
            env_var = self._check_output_strip(
                ['grep', '-z', '^DBUS_SESSION_BUS_ADDRESS',
                 '/proc/{}/environ'.format(pid)]).strip('\0')
            env_var_split = env_var.split('=', 1)

            if len(env_var_split) > 1:
                return env_var_split[1]

    def _get_existing_dbus_session(self):
        uid = os.getuid()

        self.module.debug("Trying to detect existing D-Bus user session for user: %d" % uid)
        if not psutil_found:
            return self._get_dbus_bus_address_no_psutil(uid)

        for pid in psutil.pids():
            process = psutil.Process(pid)
            process_real_uid, _, _ = process.uids()
            try:
                if process_real_uid == uid and 'DBUS_SESSION_BUS_ADDRESS' in process.environ():
                    dbus_session_bus_address_candidate = process.environ()['DBUS_SESSION_BUS_ADDRESS']
                    self.module.debug(
                        "Found D-Bus user session candidate at address: %s" % dbus_session_bus_address_candidate)
                    command = ['dbus-send', '--address=%s' % dbus_session_bus_address_candidate, '--type=signal', '/',
                               'com.example.test']
                    rc, _, _ = self.module.run_command(command)

                    if rc == 0:
                        self.module.debug(
                            "Verified D-Bus user session candidate as usable at address: %s" % dbus_session_bus_address_candidate)

                        return dbus_session_bus_address_candidate

            # This can happen with things like SSH sessions etc.
            except psutil.AccessDenied:
                pass

        self.module.debug("Failed to find running D-Bus user session, will use dbus-run-session")

        return None

    def run_command(self, command):
        if self.dbus_session_bus_address is None:
            self.module.debug("Using dbus-run-session wrapper for running commands.")
            command = ['dbus-run-session'] + command
            rc, out, err = self.module.run_command(command)

            if self.dbus_session_bus_address is None and rc == 127:
                self.module.fail_json(
                    msg="Failed to run passed-in command, dbus-run-session faced an internal error: %s" % err)
        else:
            extra_environment = {'DBUS_SESSION_BUS_ADDRESS': self.dbus_session_bus_address}
            rc, out, err = self.module.run_command(command, environ_update=extra_environment)

        return rc, out, err


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
