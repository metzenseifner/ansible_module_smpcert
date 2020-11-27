#!/bin/bash

function _create_user() {
  # Create a SSH user
  useradd -m testuser
  SSH_USERPASS=testpass
  printf "$SSH_USERPASS" | passwd testuser --stdin
  echo "SSH user password: $SSH_USERPASS"
}

function _add_user_to_sudoers() {
  echo "user ALL=(ALL:ALL) NOPASSWD: ALL" | (EDITOR="tee -a" visudo)
}

_create_user
_add_user_to_sudoers
