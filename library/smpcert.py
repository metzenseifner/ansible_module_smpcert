#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Jonathan L. Komar <komar.jonathanATgmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: smpcert
short_description: Replace CA certificate chains on SMP351s
author: "Jonathan L. Komar"
options: 
  certificate:
    description: 
      - Path to CA certificate (contains the chain of trust)
    required: true
    type: str
  backup: 
    description: 
      - Directory to backup original certificate file to path
    default: None
    type: str
    required: false
  port:
    description:
      - Select the port to connect to over SFTP.
    default: 22022
    type: int
    required: false
  username: 
    description:
      - Username for SFTP authorization.
    default: None
    type: str
    required: true
  password:
    description:
      - Password for SFTP authorization.
    default: None
    type: str
    required: true
'''

EXAMPLES = r'''
- name: Add a certificate without backup
  smpcert:
    certificate: "{{ssl/{{inventory_hostname}}.pem}}"

- name: With backup
  smpcert:
    certificate: "{{certificate}}"
    backup: "./backup"
    username: "Jiminy"
    password: "Cricket"
'''

RETURN = r'''
# TODO These are examples of possible return values, and in general should use other names for return values.
'''
