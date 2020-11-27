#!/bin/bash

if [ "${AUTHORIZED_KEYS}" != "nil" ]; then
  mkdir -p /home/testuser/.ssh
  chmod 700 /home/testuser/.ssh
  touch /home/testuser/.ssh/authorized_keys
  chmod 600 /home/testuser/.ssh/authorized_keys
  echo ${AUTHORIZED_KEYS} > /home/testuser/.ssh/authorized_keys
  chown -R user /home/testuser/.ssh
fi

if [ "${CERT}" != "nil" ]; then
  install -o testuser -m 777 /root/cacert.pem /certs/cacert.pem
fi

exec /usr/sbin/init
