# Handle $0 according to the standard:
# https://zdharma-continuum.github.io/Zsh-100-Commits-Club/Zsh-Plugin-Standard.html
0="${${ZERO:-${0:#$ZSH_ARGZERO}}:-${(%):-%N}}"
0="${${(M)0:#/*}:-$PWD/$0}"

__FZF_SETTINGS_DIR="${0:A:h}"

__icon_root=$(echo -e '\uf115')

__zshz_list() {
  z|awk '{print $2}'|tac|python3 $__FZF_SETTINGS_DIR/zshz-formatter.py
}

__subdir_list() {
  find -L . -mindepth 1 \( -path '*/\.*' -o -fstype 'sysfs' -o -fstype 'devfs' -o -fstype 'devtmpfs' -o -fstype 'proc' \) -prune \
    -o -type d -print 2> /dev/null|cut -b3-|awk -v icon=$__icon_root '{print "\x1b[38;5;22m[\x1b[38;5;230md"++cnt"\x1b[38;5;22m]\x1b[38;5;230m "icon"  "$1}'
}

FZF_ALT_C_COMMAND='{__zshz_list; __subdir_list}'
FZF_ALT_C_OPTS="--ansi --bind 'enter:become(echo {3})'" # get 3rd column to remove decorations

FZF_CTRL_T_OPTS="
  --preview 'bat -n --color=always {}'
  --bind 'ctrl-/:change-preview-window(down|hidden|)'
  --color header:italic
  --header '<tab> to select, <enter> to finish, <ctrl-/> to change preview'
  --height 70%"
