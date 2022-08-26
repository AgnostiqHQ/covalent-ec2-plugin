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
import covalent as ct

executor = ct.executor.EC2Executor(
    username=os.getenv("SSH_EXECUTOR_USERNAME", "ubuntu"),
    profile=os.getenv("AWS_PROFILE", "default"),
    credentials_file=os.getenv("AWS_SHARED_CREDENTIALS_FILE"),
    key_name=os.getenv("KEY_PAIR_NAME"),
    ssh_key_file=os.getenv("SSH_EXECUTOR_SSH_KEY_FILE"),
    vpc="",
    subnet="",
    cache_dir="/tmp"
)
