# # Copyright 2021 Agnostiq Inc.
# #
# # This file is part of Covalent.
# # 
# # Licensed under the GNU Affero General Public License 3.0 (the "License"). 
# # A copy of the License may be obtained with this software package or at
# #
# #      https://www.gnu.org/licenses/agpl-3.0.en.html
# #
# # Use of this file is prohibited except in compliance with the License. Any 
# # modifications or derivative works of this file must retain this copyright 
# # notice, and modified files must contain a notice indicating that they have 
# # been altered from the originals.
# #
# # Covalent is distributed in the hope that it will be useful, but WITHOUT
# # ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# # FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
# #
# # Relief from the License may be granted by purchasing a commercial license.

# # Ignore results folders

import os
from covalent_ec2_plugin.ec2 import EC2Executor


def init_executor():
    profile = os.environ.get('AWS_PROFILE') or 'default'
    credentials = "~/.aws/credentials"
    ssh_key_file = os.environ.get('SSH_KEY_FILE')
    key_name = ssh_key_file.split('/')[-1].split('.')[0]

    executor = EC2Executor(
        profile=profile,
        credentials_file=credentials,
        key_name=key_name,
        ssh_key_file=ssh_key_file,
        vpc="",
        subnet="",
        cache_dir="/tmp"
    )

    return executor
