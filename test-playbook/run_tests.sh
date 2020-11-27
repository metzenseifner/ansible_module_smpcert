#!/bin/bash

DOCKER_IMAGE="local/centos7-systemd"
DOCKER_CONTAINER_NO_CERT="smpcert-test-no-cert"
DOCKER_CONTAINER_WITH_CERT="smpcert-test-with-cert"
DOCKER_CONTAINER_NO_CERT_PORT=22022
DOCKER_CONTAINER_WITH_CERT_PORT=22023

docker ps
statuscode=$?
if [[ ! "$statuscode" -eq 0 ]];then
  echo "Ensure docker daemon is running and that the image $DOCKER_IMAGE is available."
  exit 1
fi

function setUp() {
docker rm -f "$DOCKER_CONTAINER_NO_CERT"
docker rm -f "$DOCKER_CONTAINER_WITH_CERT"
docker run -ti --privileged --name $DOCKER_CONTAINER_NO_CERT -d -p $DOCKER_CONTAINER_NO_CERT_PORT:22 "$DOCKER_IMAGE"
docker run -ti --privileged --name $DOCKER_CONTAINER_WITH_CERT -d -p $DOCKER_CONTAINER_WITH_CERT_PORT:22 -e CERT="yes" "$DOCKER_IMAGE"
echo "==> Sleeping for 4s (quick hack to wait for container to start)"
sleep 4
}

function tearDown() {
docker rm -f "$DOCKER_CONTAINER_NO_CERT"
docker rm -f "$DOCKER_CONTAINER_WITH_CERT"
}


# WARNING
# SftpSession could not instantiate: AuthenticationException('Authentication failed.
# --> Also means that the sftp server did not have time to start.

for playbook in playbooks/test-*.yml; do
  setUp
  ansible-playbook "$playbook" -vvv
  tearDown
done
