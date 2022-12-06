#!/usr/bin/env python

# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the GNU Affero General Public License 3.0 (the "License").
# A copy of the License may be obtained with this software package or at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html
#
# Use of this file is prohibited except in compliance with the License. Any
# modifications or derivative works of this file must retain this copyright
# notice, and modified files must contain a notice indicating that they have
# been altered from the originals.
#
# Covalent is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
#
# Relief from the License may be granted by purchasing a commercial license.

from dotenv import load_dotenv

load_dotenv()

import os

import covalent as ct

executor_config = {
    "username": os.getenv("executor_username", "ubuntu"),
    "credentials_file": os.getenv("executor_credentials_file", "~/.aws/credentials"),
    "ssh_key_file": os.getenv("executor_ssh_key_file", ""),
    "vpc": os.getenv("executor_vpc"),
    "subnet": os.getenv("executor_subnet"),
    "cache_dir": "/tmp",
}

print("Executor Configuration:")
print(executor_config)

executor = ct.executor.EC2Executor(**executor_config)