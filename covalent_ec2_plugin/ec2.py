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

import subprocess
import os
from typing import Any, Callable, Dict, List, Tuple
import boto3, botocore
from multiprocessing import Queue as MPQ

# Covalent imports
from covalent._results_manager.result import Result
from covalent._shared_files import logger


# The EC2Executor should inherit from the SSH Executor
from covalent.executor.ssh import SSHExecutor

app_log = logger.app_log
log_stack_info = logger.log_stack_info

# The plugin class name must be given by the EXECUTOR_PLUGIN_NAME attribute. In case this
# module has more than one class defined, this lets Covalent know which is the executor class.
executor_plugin_name = "EC2Executor"

_EXECUTOR_PLUGIN_DEFAULTS = {
    "username": "",
    "hostname": "",
    "ssh_key_file": os.path.join(os.environ["HOME"], ".ssh/id_rsa") or "",
    "profile": os.environ.get("AWS_PROFILE") or "",
    "credentials_file": os.path.join(os.environ["HOME"], ".aws/credentials"),
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
        username: username used by an SSH client to authenticate to the instance.
        hostname: The public DNS name of the instance
        profile: The name of the AWS profile
        credentials_file: Filename of the credentials file used for authentication to AWS.
        ssh_key_file: Filename of the private key used for authentication with the remote server if it exists.
        run_local_on_ec2_fail: If True, and the execution fails to run on the instance,
            then the execution is run on the local machine.
        _INFRA_DIR: The path to the directory containing the terraform configuration files
        _BUCKET_NAME: The name of the AWS S3 bucket used in manipulating result objects.
        _BUCKET_REGION: The location of the S3 bucket
        kwargs: Key-word arguments to be passed to the parent class (SSHExecutor)
    """
    _INFRA_DIR = "../infra"
    _BUCKET_NAME = "covalent-ec2-executor-bucket"
    _BUCKET_REGION = "ca-central-1"

    def __init__(
            self,
            username: str,
            hostname: str,
            profile: str,
            credentials_file: str,
            ssh_key_file: str = os.path.join(os.environ["HOME"], ".ssh/id_rsa"),
            **kwargs
    ) -> None:
        self.username = username
        self.hostname = hostname
        self.profile = profile
        self.credentials_file = credentials_file
        self.ssh_key_file = ssh_key_file
        self.kwargs = kwargs
        super().__init__(username, hostname, **kwargs)

    def setup(self) -> Any:
        """
        Calls Terraform code to setup the infrastructure for EC2
        Terraform processes the config parameters defined in "aws user_data" for deploying resources such
        as the bucket for storing pickled result objects and the vpc that hosts the instance.
        Args:
            region: The region where the bucket is deployed
        """
        try:
            session = boto3.Session(profile_name=self.profile)
            client = session.client('s3')
            if client.head_bucket(Bucket=self._BUCKET_NAME):
                app_log.log(level=1, msg=f"{self._BUCKET_NAME} already exists.")

            else:
                client.create_bucket(
                    ACL='public-read-write',
                    Bucket=self._BUCKET_NAME,
                    CreateBucketConfiguration={
                        'LocationConstraint': self._BUCKET_REGION
                    },

                    ObjectOwnership='BucketOwnerPreferred',
                )
        except botocore.exceptions.ClientError as e:
            app_log.error(e)

        # subprocess.run(["terraform", "init"], cwd=self._INFRA_DIR)
        # subprocess.run(["terraform", "plan", "-auto-approve"], cwd=self._INFRA_DIR)
        # subprocess.run(["terraform", "apply"], cwd=self._INFRA_DIR)

    def teardown(self, info_dict: dict) -> Any:
        """
        Terminates the running instance after workflow execution and destroys all supporting resources
        """

        subprocess.run(["terraform", "destroy"], cwd=self._INFRA_DIR)
        subprocess.run(["aws", "s3", "rb", f"s3://{self._BUCKET_NAME}", "--force", f"--profile={self.profile}"])
        return info_dict

    def run(self, function: Callable, args: List, kwargs: Dict):

        """
        Runs the executable function and manipulates the result object
        - pickle function and upload to S3 bucket
        - terraform init and run
        - Download pickle file using aws s3 cp, unpickle, and run the code
        - Generate and pickle res obj and uploads back to s3
        """

        # Attempt to connect via SSH
        try:
            if not self._client_connect():
                # Attempt to connect via public IP address ( to be implemented)
                pass
        except ConnectionError as e:
            app_log.error(e)

    def execute(
            self,
            function: Any,
            args: list,
            kwargs: dict,
            dispatch_id: str,
            results_dir: str,
            node_id: int = -1,
            info_queue: MPQ = None,
    ) -> Any:
        self.setup()
        self.run(function=function, args=args, kwargs=kwargs)
        self.teardown()
        return None

    def get_status(self, info_dict: dict) -> Result:
        """
        Get the current status of the task.

        Args:
            info_dict: a dictionary containing any necessary parameters needed to query the
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
