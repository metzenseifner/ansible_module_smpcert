#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import utils
from ansible.plugins.action import ActionBase
import paramiko
import os
from datetime import datetime
import logging
import stat
logger = logging.getLogger(__name__)

class SftpSession():
  def __init__(self, host, port, username, password):
    if host is None:
      raise ArgumentException(f"invalid host: {host}")
    if port is None:
      raise TypeError(f"invalid port: {port}")
    if username is None:
      raise TypeError(f"invalid username: {username}")
    if password is None:
      raise TypeError(f"invalid password: {password}")
    self.host =  host
    self.port = port
    self.username = username
    self.password = password
    try: 
      logger.debug(f"calling paramiko.Transport({self.host}, {self.port})")
      self.transport = paramiko.Transport((self.host, self.port))
      self.transport.connect(hostkey=None)
      self.transport.set_hexdump(True) # Debug
      self.transport.auth_password(self.username, self.password)
      self.sftpclient = paramiko.SFTPClient.from_transport(self.transport)
    except Exception as e:
      raise Exception("{} could not instantiate: {}".format(self.__class__.__name__, repr(e))) 
      exit(1)

  def is_file(self, path) -> (bool, str):
    try: 
      stat_attrs = self.sftpclient.stat(path)
      if stat.S_ISREG(stat_attrs.st_mode):
        return (True, "") 
      return (False, f"stat.S_ISFILE failed. No file at {path}.")
    except FileNotFoundError as f:
      return (False, f"{repr(f)}")
    except Exception as e:
      return (False, f"{repr(e)}")

  def read_file_bytes(self, path) -> (bytes, str):
    try: 
      with self.sftpclient.open(path, "rb") as sftp_file:
        bytesRead = bytes()
        buffer = bytes()
        while (buffer := sftp_file.read()) != b"":
          bytesRead = bytesRead + buffer
        return (bytesRead, "")
    except Exception as e:
      return (None, repr(e))

  def get(self, remotepath, localpath, callback=None) -> (bool, str):
    """Delegate to SFTPClient.get
    """
    try:
      self.sftpclient.get(remotepath,localpath,callback=callback)
      return (True, "")
    except Exception as e:
      return (False, f"{repr(e)}")

  def write_file(self, fPath, target) -> (bool, str):
    try:
      self.sftpclient.put(fPath, target, confirm=True)
      return (True, "")
    except Exception as e:
      return (False, repr(e))

def compare_md5(file1, file2) -> bool:
  """Compare using md5 checksum

      0 if same
      -1 if first path greater
      1 if second path greater
  """
  import hashlib
  md5_hash1 = hashlib.md5() # obj1
  md5_hash2 = hashlib.md5() # obj2
  md5_hash1.update(file1)
  md5_hash2.update(file2)
  if md5_hash1.hexdigest() == md5_hash2.hexdigest():
    return 0
  return 1 if md5_hash1.hexdigest() < md5_hash2.hexdigest() else -1

def read_file_bytes(path) -> (bytes, str):
  try:
    with open(path, "rb") as fh:
      bytesRead = bytes()
      buffer = bytes()
      while (buffer := fh.read()) != b"":
        bytesRead = bytesRead + buffer
      return (bytesRead, "")
  except Exception as e:
    return (None, repr(e))

def write_local_file(content, path) -> bool:
  try:
    if os.path.exists(path):
      raise Exception(f"File already exists at {path}")
    with open(path,"wb") as fh:
      fh.write(content)
    return True
  except Exception as e:
    print(repr(e))
    return False

def abort(result:dict, msg:str) -> dict:
  result['failed'] = True
  result['msg'] = msg
  return result

class ActionModule(ActionBase):
  '''
    Provides functionality on master node.
  '''
  # ActionBase uses this to determine at which point in execution temporary directories need to be available.
  # If Action Plugin uses other modules to transfer files.
  TRANSFERS_FILES = False
  SMP_CERT_PATH = '/certs/cacert.pem'

  def _merge_args(self, module_args, complex_args):
    args = {}
    if complex_args:
      args.update(complex_args)

    kv = utils.parse_kv(module_args)
    args.update(kv)

  def run(self, tmp=None, task_vars=None):
    ''' Handler for smpcert operations 

        :kwarg task_vars: The variables (host vars, group vars, config vars, etc. and facts from the host).
                    Use facts with caution because the user can disable them. If they are absolutely
                    necessary, use the setup module explicitly here.
        :kwarg tmp: (deprecated) 
    '''
    if task_vars is None:
      task_vars = dict()

    # dict() unless subclassed, then inherits
    result = super(ActionModule, self).run(tmp, task_vars)
    del tmp # deprecated and has no effect

    # self._task.args is dict of yaml
    certificate = self._task.args.get('certificate', None)
    backup_dir = self._task.args.get('backup', None)
    # task_vars is dict of everything else
    host = task_vars.get('inventory_hostname', None)
    port = task_vars.get('port', 22022)
    username = task_vars.get('username', None)
    password = task_vars.get('password', None)

    if not certificate:
      return abort(result, 'certificate is required')
    result['local_cert_path'] = certificate

    local_cert = read_file_bytes(certificate)
    if local_cert[0] is None:
      return abort(result, local_cert[1])

    try:
      session = SftpSession(host, port, username, password)
    except Exception as e:
      return abort(result, repr(e))
    
    # Decide early whether remote has cert
    remote_cert_exists = session.is_file(ActionModule.SMP_CERT_PATH)
    result['remote_cert_exists'] = remote_cert_exists[0]

    # Handle Backup
    if remote_cert_exists[0] is True and backup_dir is not None:
      backup_path = os.path.join(backup_dir, "{}_{}.pem".format(host, datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")))
      if not os.path.isdir(backup_dir):
        return abort(result, f"The given backup directory does not exist: {backup_dir}. File would have been {backup_path}.")
      result['backup_path'] = backup_path
      backup_result = session.get(ActionModule.SMP_CERT_PATH, backup_path)
      if backup_result[0] is False:
        return abort(result, f"error writing backup file: {backup_result[1]}")
    else:
      result['backup_warning'] = "Because no backup directory was provided, there will be no backup of the remote certificate."

    # Handle Certificate Swap 
    if remote_cert_exists[0] is True:
      remote_cert =  session.read_file_bytes(ActionModule.SMP_CERT_PATH)
      if remote_cert[0] is not None:
        compareResult = compare_md5(local_cert[0], remote_cert[0])
        if compareResult == 0:
          result['msg'] = "No changes necessary because the local certificate matches the remote certificate."
          return result
        else:
          result['notice'] = "Local certificate differs from remote certificate."
      else:
        abort(result, f"Error reading remote certificate: {remote_cert}")
    else:
      result['certificate_update_msg'] = "No certificate detected on remote. Certificate will be updated."

    try:
      rs = session.write_file(certificate, ActionModule.SMP_CERT_PATH)
      result['msg'] = f"Wrote {certificate} to {host}:{ActionModule.SMP_CERT_PATH}"
      result['changed'] = True
      if rs[0] is False:
        abort(result, f"Failed to write file to {host}:{ActionModule.SMP_CERT_PATH}: {rs[1]}")
    except Exception as e:
      return abort(result, repr(e)) 

    return result 
