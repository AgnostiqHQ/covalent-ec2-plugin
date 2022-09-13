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
import uuid
from tests.create_executor import executor as ec2_exec


async def test_setup_teardown() -> None:

    """Tests whether setup() and teardown() can correctly create and destroy resources, respectively"""

    dispatch_id = str(uuid.uuid1())
    node_id = '0'
    task_metadata = {"dispatch_id": dispatch_id, "node_id": node_id}

    try:
        await ec2_exec.setup(task_metadata=task_metadata)
    except Exception as e:
        raise RuntimeError(f"Terraform failed to create the required resources and raised an error {e}")

    test_state_file = os.path.join(ec2_exec.cache_dir, f"{dispatch_id}-{node_id}.tfstate")

    assert os.path.exists(test_state_file) is True

    try:
        await ec2_exec.teardown(task_metadata=task_metadata)
    except Exception as e:
        raise RuntimeError(f"Terraform failed to destroy the provisioned resources and raised an error {e}")
    os.remove(test_state_file)





