import unittest
import sys
sys.path.append('..')
from smpcert import *
import paramiko
import time
import subprocess
import logging

HOST = 'localhost'
PORT_WITH_CERT= 47444
PORT_NO_CERT = 47445
USERNAME = 'testuser'
PASSWORD = 'testpass'

DOCKER_BIN="/usr/bin/docker"
DOCKER_IMAGE='local/centos7-systemd'
DOCKER_CONTAINER_NAME_WITH_CERT="test-smpcert-impl-with-cert"
DOCKER_CONTAINER_NAME_NO_CERT="test-smpcert-impl-no-cert"
REMOTE_CERT_PATH='/certs/cacert.pem'
LOCAL_CERT_PATH='./ssl/cacert.pem'

DOCKER_START_NO_CERT=[f'{DOCKER_BIN}', 'run', '-ti', '--privileged', '--name', f'{DOCKER_CONTAINER_NAME_NO_CERT}', '-d', '-p', f'{PORT_NO_CERT}:22', f'{DOCKER_IMAGE}']
DOCKER_START_WITH_CERT=[f'{DOCKER_BIN}', 'run', '-ti', '--privileged', '--name', f'{DOCKER_CONTAINER_NAME_WITH_CERT}', '-d', '-p', f'{PORT_WITH_CERT}:22', '-e', f'CERT=yes', f'{DOCKER_IMAGE}',]
DOCKER_STOP_WITH_CERT=[f'{DOCKER_BIN}', 'rm', '-f', f'{DOCKER_CONTAINER_NAME_WITH_CERT}']
DOCKER_STOP_NO_CERT=[f'{DOCKER_BIN}', 'rm', '-f', f'{DOCKER_CONTAINER_NAME_NO_CERT}']

def run_cmd(cmd, delay=0):
  subprocess.call(cmd)
  time.sleep(delay)

class SftpTestCase(unittest.TestCase):

  def setUp(self):
    run_cmd(DOCKER_STOP_WITH_CERT)
    run_cmd(DOCKER_STOP_NO_CERT)
    run_cmd(DOCKER_START_WITH_CERT, 4) 
    run_cmd(DOCKER_START_NO_CERT, 4) 

  def tearDown(self):
    run_cmd(DOCKER_STOP_WITH_CERT)
    run_cmd(DOCKER_STOP_NO_CERT)

  def test_local_read_file(self):
    logger = logging.getLogger("test_local_read_file")
    local_file = read_file_bytes('./ssl/dummy')
    self.assertIsInstance(local_file, tuple)
    logger.info(f"local_file: {type(local_file)} {local_file}")
    self.assertEqual(local_file[0], b"123")
    
  def test_sftp_get_file_when_with_remote_cert(self):
    session = SftpSession(HOST, PORT_WITH_CERT, USERNAME, PASSWORD)
    remote_file = session.read_file_bytes(REMOTE_CERT_PATH)
    local_file = read_file_bytes(LOCAL_CERT_PATH)
    self.assertIsNotNone(local_file[0])
    self.assertIsNotNone(remote_file[0])
    self.assertEqual(remote_file[0], local_file[0])

  def test_sftp_get_file_when_no_remote_cert(self):
    session = SftpSession(HOST, PORT_NO_CERT, USERNAME, PASSWORD)
    remote_file = session.read_file_bytes(REMOTE_CERT_PATH)
    local_file = read_file_bytes(LOCAL_CERT_PATH)
    self.assertIsNone(remote_file[0])

  def test_sftp_write_file_when_no_remote_cert(self):
    session = SftpSession(HOST, PORT_NO_CERT, USERNAME, PASSWORD)
    local_file = read_file_bytes(LOCAL_CERT_PATH)
    session.write_file(LOCAL_CERT_PATH, REMOTE_CERT_PATH)
    remote_file = session.read_file_bytes(REMOTE_CERT_PATH)
    self.assertEqual(remote_file[0], local_file[0])
    
  def test_is_file_when_with_remote_cert(self):
    session = SftpSession(HOST, PORT_WITH_CERT, USERNAME, PASSWORD)
    remote_file = session.is_file(REMOTE_CERT_PATH)
    self.assertTrue(remote_file[0])

  def test_is_file_when_no_remote_cert(self):
    session = SftpSession(HOST, PORT_NO_CERT, USERNAME, PASSWORD)
    remote_file = session.is_file(REMOTE_CERT_PATH)
    self.assertFalse(remote_file[0])

if __name__ == "__main__":
  logging.basicConfig(stream=sys.stdout, level="INFO")
  unittest.main()
