export FZF_CTRL_T_OPTS="
  --preview 'bat -n --color=always {}'
  --bind 'ctrl-/:change-preview-window(down|hidden|)'
  --color header:italic
  --header '<tab> to select, <enter> to finish, <ctrl-/> to change preview'
  --height 70%"

