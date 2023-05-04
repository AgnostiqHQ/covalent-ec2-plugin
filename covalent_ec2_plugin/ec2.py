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

import asyncio
import copy
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Tuple, Union

import boto3
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
        "profile": "",
        "credentials_file": "",
        "region": "",
        "instance_type": "t2.micro",
        "volume_size": "8",
        "vpc": "",
        "subnet": "",
        "key_name": "",
        "conda_env": "covalent",
    }
)

EC2_KEYPAIR_NAME = "covalent-ec2-keypair"
EC2_SSH_DIR = "~/.ssh/covalent"


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

    _TF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "infra"))

    def __init__(
        self,
        profile: str = None,
        key_name: str = None,
        username: str = None,
        hostname: str = None,
        credentials_file: str = None,
        region: str = None,
        instance_type: str = "t2.micro",
        volume_size: int = 8,
        vpc: str = "",
        subnet: str = "",
        conda_env: str = "covalent",
        **kwargs,
    ) -> None:

        username = username or get_config("executors.ec2.username")
        hostname = hostname or get_config("executors.ec2.hostname")
        profile = profile or get_config("executors.ec2.profile")
        credentials_file or get_config("executors.ec2.credentials_file")
        region = region or get_config("executors.ec2.region")

        AWSExecutor.__init__(
            self=self, profile=profile, region=region, credentials_file=credentials_file
        )
        SSHExecutor.__init__(
            self=self,
            username=username,
            hostname=hostname,
            conda_env=conda_env,
            **kwargs,
        )

        # as executor instance is reconstructed the below values are seemingly lost, added back here as a temp fix
        self.profile = profile or get_config("executors.ec2.profile")
        self.region = region or get_config("executors.ec2.region")
        self.credentials_file = credentials_file or get_config("executors.ec2.credentials_file")

        self.key_name = (
            key_name
            or kwargs.get("ssh_key_file", "").split("/")[-1].split(".")[0]
            or get_config("executors.ec2.key_name")
        )
        self.instance_type = instance_type or get_config("executors.ec2.instance_type")
        self.volume_size = volume_size or get_config("executors.ec2.volume_size")
        self.vpc = vpc or get_config("executors.ec2.vpc")
        self.subnet = subnet or get_config("executors.ec2.subnet")

    async def _run_async_subprocess(self, cmd: List[str], cwd=None, log_output: bool = False):

        proc = await asyncio.create_subprocess_shell(
            " ".join(cmd), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd
        )

        if log_output:
            stdout_chunks = []
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                line_str = line.decode("utf-8").strip()
                stdout_chunks.append(line_str)
                app_log.debug(line_str)

            _, stderr = await proc.communicate()
            stderr = stderr.decode("utf-8").strip()
            stdout = os.linesep.join(stdout_chunks)

        else:
            stdout, stderr = await proc.communicate()
            stdout = stdout.decode("utf-8").strip()
            stderr = stderr.decode("utf-8").strip()

        if proc.returncode != 0:
            app_log.debug(stderr)
            raise subprocess.CalledProcessError(proc.returncode, cmd, stdout, stderr)

        return proc, stdout, stderr

    def _get_tf_statefile_path(self, task_metadata: Dict) -> str:
        state_file = f"{self.cache_dir}/ec2-{task_metadata['dispatch_id']}-{task_metadata['node_id']}.tfstate"
        return state_file

    async def _get_tf_output(self, var: str, state_file: str) -> str:
        _, value, _ = await self._run_async_subprocess(
            ["terraform", "output", "-raw", f"-state={state_file}", var], cwd=self._TF_DIR
        )
        return value

    async def setup(self, task_metadata: Dict) -> None:
        """
        Invokes Terraform to provision supporting resources for the instance

        """

        # Init Terraform (doing this in a blocking manner to avoid race conditions during init, better way would to be use asyncio
        # locks or to ensure that terraform init is run just once)
        subprocess.run(["terraform init"], cwd=self._TF_DIR, shell=True, check=True)

        state_file = self._get_tf_statefile_path(task_metadata)

        boto_session = boto3.Session(**self.boto_session_options())
        profile = boto_session.profile_name
        region = boto_session.region_name

        ec2 = boto_session.client("ec2")
        self.key_name = EC2_KEYPAIR_NAME

        # Create dir if it doesn't exist
        ec2_ssh_dir = Path(EC2_SSH_DIR).expanduser().resolve()
        ec2_ssh_dir.mkdir(parents=True, exist_ok=True)

        self.ssh_key_file = str(ec2_ssh_dir / f"{self.key_name}.pem")

        # Try to import the key pair/ssh key file that might've been created earlier
        # If those don't exist, create the key pair and save the key material to the ssh_key_file
        if not Path(self.ssh_key_file).exists():
            try:
                key_pair = ec2.create_key_pair(KeyName=self.key_name)
            except Exception as e:
                if e.response["Error"]["Code"] != "InvalidKeyPair.Duplicate":
                    raise e

                app_log.info(
                    f"Key pair {self.key_name} already exists, deleting and creating a new one"
                )
                ec2.delete_key_pair(KeyName=self.key_name)
                key_pair = ec2.create_key_pair(KeyName=self.key_name)

            with open(self.ssh_key_file, "w") as f:
                f.write(str(key_pair["KeyMaterial"]))
            os.chmod(self.ssh_key_file, 0o400)

        # Apply Terraform Plan
        base_cmd = [
            "terraform",
            "apply",
            "-auto-approve",
            f"-state={state_file}",
        ]

        self.infra_vars = [
            f"-var=aws_region={region}",
            f"-var=aws_profile={profile}",
            f"-var=name=covalent-ec2-task-{task_metadata['dispatch_id']}-{task_metadata['node_id']}",
            f"-var=instance_type={self.instance_type}",
            f"-var=disk_size={self.volume_size}",
            f"-var=key_file={self.ssh_key_file}",
            f"-var=key_name={self.key_name}",
        ]

        if self.credentials_file:
            self.infra_vars += [f"-var=aws_credentials={self.credentials_file}"]

        if self.vpc:
            self.infra_vars += [f"-var=vpc_id={self.vpc}"]
        if self.subnet:
            self.infra_vars += [f"-var=subnet_id={self.subnet}"]

        cmd = base_cmd + self.infra_vars

        app_log.debug(f"Running Terraform setup command: {cmd}")

        await self._run_async_subprocess(cmd, cwd=self._TF_DIR, log_output=True)

        # Get Hostname from Terraform Output
        self.hostname = await self._get_tf_output("hostname", state_file)

        # Get Username from Terraform Output
        self.username = await self._get_tf_output("username", state_file)

        # Get Remote Cache from Terraform Output
        self.remote_cache = await self._get_tf_output("remote_cache", state_file)

    async def teardown(self, task_metadata: Dict) -> None:
        """
        Invokes Terraform to terminate the instance and teardown supporting resources
        """

        state_file = self._get_tf_statefile_path(task_metadata)

        if not os.path.exists(state_file):
            raise FileNotFoundError(
                f"Could not find Terraform state file: {state_file}. Infrastructure may need to be manually deprovisioned."
            )

        base_cmd = ["terraform", "destroy", "-auto-approve", f"-state={state_file}"]
        cmd = base_cmd + self.infra_vars

        app_log.debug(f"Running teardown Terraform command: {cmd}")

        await self._run_async_subprocess(cmd, cwd=self._TF_DIR, log_output=True)

        # Delete the state file
        os.remove(state_file)
        os.remove(f"{state_file}.backup")
