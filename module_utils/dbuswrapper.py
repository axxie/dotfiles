import os
import subprocess
import traceback

PSUTIL_IMP_ERR = None

try:
    import psutil
    psutil_found = True
except ImportError:
    PSUTIL_IMP_ERR = traceback.format_exc()
    psutil_found = False


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
