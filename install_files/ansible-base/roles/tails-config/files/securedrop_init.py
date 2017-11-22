#!/usr/bin/python

import os
import sys
import subprocess


# check for root
if os.geteuid() != 0:
    sys.exit('You need to run this as root')

# paths
path_torrc_additions = '/home/amnesia/Persistent/.securedrop/torrc_additions'
path_torrc_backup = '/etc/tor/torrc.bak'
path_torrc = '/etc/tor/torrc'

# load torrc_additions
if os.path.isfile(path_torrc_additions):
    torrc_additions = open(path_torrc_additions).read()
else:
    sys.exit('Error opening {0} for reading'.format(path_torrc_additions))

# load torrc
if os.path.isfile(path_torrc_backup):
    torrc = open(path_torrc_backup).read()
else:
    if os.path.isfile(path_torrc):
        torrc = open(path_torrc).read()
    else:
        sys.exit('Error opening {0} for reading'.format(path_torrc))

    # save a backup
    open(path_torrc_backup, 'w').write(torrc)

# append the additions
open(path_torrc, 'w').write(torrc + torrc_additions)

# reload tor
try:
    subprocess.check_call(['systemctl', 'reload', 'tor@default.service'])
except subprocess.CalledProcessError:
    sys.exit('Error reloading Tor')

# Turn off "automatic-decompression" in Nautilus to ensure the original
# submission filename is restored (see
# https://github.com/freedomofpress/securedrop/issues/1862#issuecomment-311519750).
subprocess.call(['/usr/bin/dconf', 'write',
                 '/org/gnome/nautilus/preferences/automatic-decompression',
                 'false'])

# Set journalist.desktop and source.desktop links as trusted with Nautilus (see
# https://github.com/freedomofpress/securedrop/issues/2586)
#Set environment variables and euid to amnesia user
uid=int(os.getenv("SUDO_UID"))
gid=int(os.getenv("SUDO_GID"))
home = os.getenv("HOME")
logname = os.getenv("LOGNAME")
os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
os.environ["XDG_DATA_DIRS"] = "/usr/share/gnome:/usr/local/share/:/usr/share/"
os.environ["HOME"]="/home/amnesia"
os.environ["LOGNAME"]="amnesia"
os.setresgid(gid, gid, -1)
os.setresuid(uid, uid, -1)
subprocess.call(['rm', '/home/amnesia/Desktop/journalist.desktop'])
subprocess.call(['rm', '/home/amnesia/Desktop/source.desktop'])
subprocess.call(['ln', '-s', '/lib/live/mount/persistence/TailsData_unlocked/dotfiles/Desktop/journalist.desktop', '/home/amnesia/Desktop/journalist.desktop'])
subprocess.call(['ln', '-s', '/lib/live/mount/persistence/TailsData_unlocked/dotfiles/Desktop/source.desktop', '/home/amnesia/Desktop/source.desktop'])
subprocess.call(['gio', 'set', '/home/amnesia/Desktop/journalist.desktop', 'metadata::trusted', 'yes'])
subprocess.call(['gio', 'set', '/home/amnesia/Desktop/source.desktop', 'metadata::trusted', 'yes'])

os.environ["HOME"] = home
os.environ["LOGNAME"] = logname

# reacquire uid0 and notify the user
os.setresuid(0,0,-1)
os.setresgid(0,0,-1)
subprocess.call(['tails-notify-user',
                 'SecureDrop successfully auto-configured!',
                 'You can now access the Journalist Interface.\nIf you are an admin, you can now SSH to the servers.'])
