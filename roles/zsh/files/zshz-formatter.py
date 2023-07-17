import sys
import zlib
import subprocess
import os

icon_folder='\uf07c  '
icon_root='\uf115  '
icon_pwd='\uea9c  '
color_yellow='\x1b[38;5;228m'
color_lt_yellow='\x1b[38;5;230m'
color_lt_gray='\x1b[38;5;254m'
color_dk_green='\x1b[38;5;22m'
color_reset='\x1b[0m'
color_white='\x1b[1m\x1b[38;5;15m'

try:
    width = int(subprocess.check_output(['tput', 'cols']).decode())
except:
    width = 80

cwd = os.getcwd()

for input in sys.stdin:
    l = input.strip()
    w = len(l)
    checksum = zlib.adler32(l.strip().encode()) >> 16
    shortcut = chr(97 + checksum % 26) + chr(97 + (checksum // 26) % 26)

    if l.startswith(cwd):
        if l == cwd:
            l = color_lt_yellow + icon_pwd + l + color_reset
        else:
            r = l.removeprefix(cwd + '/')
            l = color_yellow + icon_folder + r + color_reset
            w = len(r)
    else:
        l = color_lt_gray + icon_root + l + color_reset

    shortcut_offset = max(0, width - w - 15)    
    print(f'{color_dk_green}[{color_white}{shortcut}{color_reset}{color_dk_green}]{color_reset} {l} {color_dk_green}{shortcut:>{shortcut_offset}}')
