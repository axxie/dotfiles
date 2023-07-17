function _expand_de {
  if [[ $BUFFER == "de" ]] ;then
    LBUFFER="docker exec -i -t "
    RBUFFER=" /bin/bash"
  else
    zle expand-or-complete
  fi
}

zle -N _expand_de
bindkey "^i" _expand_de
