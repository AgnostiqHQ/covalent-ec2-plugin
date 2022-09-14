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

import copy
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union

from covalent._shared_files import logger
from covalent._shared_files.config import get_config
from covalent_aws_plugins import AWSExecutor
from covalent_ssh_plugin.ssh import _EXECUTOR_PLUGIN_DEFAULTS as _SSH_EXECUTOR_PLUGIN_DEFAULTS
from covalent_ssh_plugin.ssh import SSHExecutor

executor_plugin_name = "EC2Executor"

app_log = logger.app_log
log_stack_info = logger.log_stack_info

_EXECUTOR_PLUGIN_DEFAULTS = copy.deepcopy(_SSH_EXECUTOR_PLUGIN_DEFAULTS)
_EXECUTOR_PLUGIN_DEFAULTS.update(
    {
        "profile": "default",
        "credentials_file": "",
        "instance_type": "t2.micro",
        "volume_size": "8",
        "vpc": "",
        "subnet": "",
        "key_name": "",
        "conda_env": "covalent",
    }
)


class EC2Executor(SSHExecutor, AWSExecutor):
    """
    Executor class that invokes the input function on an EC2 instance
    Args:
        profile: The name of the AWS profile
        credentials_file: Filename of the credentials file used for authentication to AWS.
        key_name: Name of the AWS EC2 key pair used for authentication with the remote server if it exists.
        vpc: (optional) AWS VPC ID of any existing VPCs if any.
        subnet: (optional) AWS Subnet ID of any existing subnets if any.
        instance_type: (optional) AWS EC2 Instance type to provision for a given task. Default: t2.micro
        volume_size: (optional) The size in GB (integer) of the GP2 SSD disk to be provisioned with EC2 instance. Default: 8
        kwargs: Key-word arguments to be passed to the parent class (SSHExecutor)
    """

    _TF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "infra"))

    def __init__(
        self,
        profile: str,
        key_name: str = "",
        username: str = "",
        hostname: str = "",
        credentials_file: str = "",
        instance_type: str = "t2.micro",
        volume_size: int = 8,
        vpc: str = "",
        subnet: str = "",
        conda_env: str = "covalent",
        **kwargs,
    ) -> None:

        credentials_file = credentials_file or str(Path(credentials_file).expanduser().resolve())
        username = username or get_config("executors.ec2.username")
        hostname = hostname or get_config("executors.ec2.hostname")
        super().__init__(
            username=username,
            hostname=hostname,
            credentials_file=credentials_file,
            conda_env=conda_env,
            **kwargs,
        )

        self.profile = profile or get_config("executors.ec2.profile")
        self.key_name = key_name or get_config("executors.ec2.key_name")
        self.instance_type = instance_type or get_config("executors.ec2.instance_type")
        self.volume_size = volume_size or get_config("executors.ec2.volume_size")
        self.vpc = vpc or get_config("executors.ec2.vpc")
        self.subnet = subnet or get_config("executors.ec2.subnet")

    async def setup(self, task_metadata: Dict) -> None:
        """
        Invokes Terraform to provision supporting resources for the instance

        """
        proc = subprocess.run(["terraform", "init"], cwd=self._TF_DIR, capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8").strip())

        state_file = os.path.join(
            self.cache_dir, f"{task_metadata['dispatch_id']}-{task_metadata['node_id']}.tfstate"
        )

        base_cmd = [
            "terraform",
            "apply",
            "-auto-approve",
            f"-state={state_file}",
        ]

        self.infra_vars = [
            "-var=name=covalent-task-{dispatch_id}-{node_id}".format(
                dispatch_id=task_metadata["dispatch_id"],
                node_id=task_metadata["node_id"],
            ),
            f"-var=instance_type={self.instance_type}",
            f"-var=disk_size={self.volume_size}",
            f"-var=key_file={self.ssh_key_file}",
            f"-var=key_name={self.key_name}",
        ]

        if os.environ.get("AWS_REGION"):
            self.infra_vars += [
                f"-var=aws_region={os.environ['AWS_REGION']}",
            ]

        if self.profile:
            self.infra_vars += [f"-var=aws_profile={self.profile}"]

        if self.credentials_file:
            self.infra_vars += [f"-var=aws_credentials={self.credentials_file}"]

        if self.vpc:
            self.infra_vars += [f"-var=vpc_id={self.vpc}"]
        if self.subnet:
            self.infra_vars += [f"-var=subnet_id={self.subnet}"]

        cmd = base_cmd + self.infra_vars

        app_log.debug(f"Infra vars are {self.infra_vars}")
        app_log.debug(f"CMD run: {cmd}")

        proc = subprocess.run(cmd, cwd=self._TF_DIR, capture_output=True)

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8").strip())

        # Return instance attributes from Terraform output and assign to self
        proc = subprocess.run(
            ["terraform", "output", "-raw", f"-state={state_file}", "hostname"],
            cwd=self._TF_DIR,
            capture_output=True,
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8").strip())

        self.hostname = proc.stdout.decode("utf-8").strip()

        proc = subprocess.run(
            ["terraform", "output", "-raw", f"-state={state_file}", "username"],
            cwd=self._TF_DIR,
            capture_output=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8").strip())

        self.username = proc.stdout.decode("utf-8").strip()

        proc = subprocess.run(
            ["terraform", "output", "-raw", f"-state={state_file}", "remote_cache"],
            cwd=self._TF_DIR,
            capture_output=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8").strip())

        self.remote_cache = proc.stdout.decode("utf-8").strip()

    async def teardown(self, task_metadata: Dict) -> None:
        """
        Invokes Terraform to terminate the instance and teardown supporting resources
        """

        state_file = os.path.join(
            self.cache_dir, f"{task_metadata['dispatch_id']}-{task_metadata['node_id']}.tfstate"
        )

        if not os.path.exists(state_file):
            raise FileNotFoundError(
                f"Could not find Terraform state file: {state_file}. Infrastructure may need to be manually deprovisioned."
            )

        base_cmd = ["terraform", "destroy", "-auto-approve", f"-state={state_file}"]

        cmd = base_cmd + self.infra_vars

        app_log.debug(f"Infra vars are {self.infra_vars}")
        app_log.debug(f"CMD run: {cmd}")

        proc = subprocess.run(cmd, cwd=self._TF_DIR, capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode("utf-8").strip())

    async def _upload_task(self):
        """Upload required workflow files to an EC2 instance"""

        pass

    async def submit_task(self):
        """Submits details of a task to an executor-managed EC2 instance"""
        pass

    async def get_status(self, info_dict: dict) -> bool:
        """Retrieves the status of a running task"""
        pass

    async def _poll_task(self):
        """Polls the status of a running task"""
        pass

    async def query_result(self):
        """Query's the result object corresponding to a submitted task"""
        pass

    async def cancel(self):
        """Cancels execution of a workflow function"""

        raise NotImplementedError

    async def _validate_credentials(self) -> Union[Dict[str, str], bool]:
        """
        Validate key pair and credentials file used to authenticate to AWS and EC2

        Args:
            None
        Returns:
            boolean indicating if key pair and credentials file exist
        Raises:
            RuntimeError: if either key pair or credentials file do not exist.
        """

        if not os.path.exists(self.key_name):
            raise FileNotFoundError(f"The instance key file '{self.key_name}' does not exist.")

        if not os.path.exists(self.credentials_file):
            creds_file_suffix = self.credentials_file.split("/")[-1]
            raise FileNotFoundError(
                f"The AWS credentials file '{creds_file_suffix}' does not exist."
            )

        return True
