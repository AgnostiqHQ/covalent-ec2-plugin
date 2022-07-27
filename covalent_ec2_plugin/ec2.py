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

"""EC2 executor plugin for the Covalent dispatcher."""

import os
from typing import Any, Callable, Dict, List, Tuple

# Covalent imports
from covalent._results_manager.result import Result
from covalent._shared_files import logger
from covalent._shared_files.config import get_config, update_config
from covalent._shared_files.util_classes import DispatchInfo
from covalent._workflow.transport import TransportableObject

# The EC2Executor should inherit from the SSH Executor
from covalent.executor.executor_plugins.ssh import SSHExecutor

app_log = logger.app_log
log_stack_info = logger.log_stack_info
log_debug_info = logger.log_debug_info

# The plugin class name must be given by the EXECUTOR_PLUGIN_NAME attribute. In case this
# module has more than one class defined, this lets Covalent know which is the executor class.
EXECUTOR_PLUGIN_NAME = "EC2Executor"

_EXECUTOR_PLUGIN_DEFAULTS = {
    "region": "ca-central-1",
    "zone": "ca-central-1b",
    "profile": "default",
    "credentials_file": os.path.join(os.environ["HOME"], ".aws/credentials"),
    "instance_type": "t2.micro",
    "ebs_volume_size": "8 GiB",
    "hostname": "ami-00f881f027a6d74a0",
    "retries": 5,
    "cache_dir": os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(os.environ["HOME"], ".cache"), "covalent"
    ),
    "remote_cache_dir": ".cache/covalent",
    "python3_path": "",
    "run_local_on_ec2_fail": False,
}


class EC2Executor(SSHExecutor):
    """
    Executor class that invokes the input function on an EC2 instance
    Args:
        username: IAM account name used for authentication to AWS
        hostname: The AMI name of the instance
        region: The region where the EC2 instance is deployed
        zone:   The availability zone where the instance is deployed
        profile: The name of the AWS profile
        credentials_file: Filename of the credentials file used for authentication to AWS.
        instance_type: The type of instance
        run_local_on_ec2_fail: If True, and the execution fails to run on the instance,
            then the execution is run on the local machine.
        kwargs: Key-word arguments to be passed to the parent class (SSHExecutor)
    """

    def __init__(
        self,
        username: str,
        hostname: str,
        region: str,
        zone: str,
        profile: str,
        instance_type: str,
        credentials_file: str = os.path.join(os.environ["HOME"], ".aws/credentials"),
        run_local_on_ec2_fail: bool = False,
        **kwargs
    ) -> None:
        self.username = username
        self.hostname = hostname
        self.region = region
        self.zone = zone
        self.profile = profile
        self.instance_type = instance_type
        self.credentials_file = credentials_file
        self.run_local_on_ec2_fail = run_local_on_ec2_fail
        self.kwargs = kwargs

        # Call the BaseExecutor initialization:
        # There are a number of optional arguments to BaseExecutor
        # that could be specfied as keyword inputs to CustomExecutor.
        base_kwargs = {}
        for key, _ in self.kwargs.items():
            if key in [
                "conda_env",
                "cache_dir",
                "current_env_on_conda_fail",
            ]:
                base_kwargs[key] = self.kwargs[key]

        super().__init__(username, hostname, **base_kwargs)

    def setup(self) -> Any:
        """
        Calls Terraform code to setup the infrastructure for EC2

        """
        pass

    def teardown(self) -> Any:
        """
        Stops all running instances and destroys resources after execution
        """
        pass

    def run(self, function: Callable, args: List, kwargs: Dict):
        app_log.debug(f"Running function {function} on the instance {self.hostname}")
        return function(*args, **kwargs)

    def get_status(self, info_dict: dict) -> Result:
        """
        Get the current status of the task.

        Args:
            info_dict: a dictionary containing any neccessary parameters needed to query the
                status. For this class (LocalExecutor), the only info is given by the
                "STATUS" key in info_dict.

        Returns:
            A Result status object (or None, if "STATUS" is not in info_dict).
        """

        return info_dict.get("STATUS", Result.NEW_OBJ)

    def cancel(self, info_dict: dict = {}) -> Tuple[Any, str, str]:
        """
        Cancel the execution task.

        Args:
            info_dict: a dictionary containing any neccessary parameters
                needed to halt the task execution.

        Returns:
            Null values in the same structure as a successful return value (a 4-element tuple).
        """

        return (None, "", "", InterruptedError)

