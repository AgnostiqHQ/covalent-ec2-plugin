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
import cloudpickle as pickle
import boto3, botocore
from multiprocessing import Queue as MPQ
import paramiko
from  scp import SCPClient

# Covalent imports
from covalent._results_manager.result import Result
from covalent._shared_files import logger

from covalent.executor.ssh import SSHExecutor

app_log = logger.app_log
log_stack_info = logger.log_stack_info

# The plugin class name must be given by the EXECUTOR_PLUGIN_NAME attribute. In case this
# module has more than one class defined, this lets Covalent know which is the executor class.
executor_plugin_name = "EC2Executor"

_EXECUTOR_PLUGIN_DEFAULTS = {
    "username": "",
    "ssh_key_file": os.path.join(os.environ["HOME"], ".ssh/id_rsa") or "",
    "instance_type": "t2.micro",
    "volume_size": "8GiB",
    "ami": "amzn-ami-hvm-*-x86_64-gp2",
    "vpc": "",
    "subnet": "",
    "profile": os.environ.get("AWS_PROFILE") or "",
    "credentials_file": os.path.join(os.environ["HOME"], ".aws/credentials"),
    "cache_dir": os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(os.environ["HOME"], ".cache"), "covalent"
    ),
    "python3_path": "",
    "run_local_on_ec2_fail": False,
}

class EC2Executor(SSHExecutor):
    """
    Executor class that invokes the input function on an EC2 instance
    Args:
        username: username used by an SSH client to authenticate to the instance.
        profile: The name of the AWS profile
        credentials_file: Filename of the credentials file used for authentication to AWS.
        ssh_key_file: Filename of the private key used for authentication with the remote server if it exists.
        run_local_on_ec2_fail: If True, and the execution fails to run on the instance,
            then the execution is run on the local machine.
        _INFRA_DIR: The path to the directory containing Terraform configuration files
        kwargs: Key-word arguments to be passed to the parent class (SSHExecutor)
    """
    _INFRA_DIR = "infra"

    def __init__(
            self,
            username: str,
            hostname: str,
            profile: str,
            credentials_file: str,
            ssh_key_file: str,
            **kwargs
    ) -> None:
        self.username = username
        self.hostname = hostname
        self.profile = profile
        self.credentials_file = credentials_file
        self.ssh_key_file = ssh_key_file
        self.kwargs = kwargs
        super().__init__(username, hostname, **kwargs)

    def setup(self) -> None:
        """
        Invokes Terraform to provision supporting resources for the instance
        """
        subprocess.run(["terraform", "init"], cwd=self._INFRA_DIR)
        subprocess.run(["terraform", "plan", "-auto-approve"], cwd=self._INFRA_DIR)
        subprocess.run(["terraform", "apply"], cwd=self._INFRA_DIR)

    def teardown(self) -> None:
        """
        Terminates the running instance after workflow execution and destroys all supporting resources
        """

        subprocess.run(["terraform", "destroy"], cwd=self._INFRA_DIR)

    def run(self, function: Callable, args: List, kwargs: Dict, task_metadata: Dict) -> Any:
        
        """
        Executes the callable function on the instance and manipulates the result object
        """
        
        self.setup()
            
        dispatch_id = task_metadata['dispatch_id']
        node_id = task_metadata['node_id']
        function_file = f"func-{dispatch_id}-{node_id}.pkl"
        result_file = f"result-{dispatch_id}-{node_id}.pkl"
        script_file = f"script-{dispatch_id}-{node_id}.pkl"

        with open(function_file, "wb") as f:
            pickle.dump((function, args, kwargs), f)
        session = boto3.Session(profile_name=self.profile)
        client = session.client('s3')

        # try:
        #     with open(function_file, "rb") as f:
        #         client.upload_fileobj(f, "covalent_ec2_bucket")

        # except botocore.exceptions.ClientError as e:
        #     app_log.error(e)
        #     exit(1)

        exec_script = "\n".join(
            [
                "import os",
                "import cloudpickle as pickle",
                "import boto3",
                f"function_filename = os.path.join(/tmp/covalent/{function_file})",
                f"results_filename = os.path.join(/tmp/covalent/{result_file})",
                "s3 = boto3.client('s3')",
                f"s3.download_file('covalent_ec2_bucket', {function_file}, function_filename)",
                "with open(function_filename, 'rb') as f_in:",
                "   function, args, kwargs = pickle.load(f_in)",
                "result = function(*args, **kwargs)",
                "with open(results_filename,'wb') as f_out:",
                "    pickle.dump(result, f_out)",
                f"s3.upload_file(results_filename, 'covalent_ec2_bucket', {result_file})",
                "",
            ]
        )

        with open(script_file, "w") as f:
            f.write(exec_script)
            
        self.client = paramiko.SSHClient() 
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
         # Attempt to connect to instance via SSH
        try:
            self._client_connect()
        except Exception as e:
            app_log.error(e)
        
        scp = SCPClient(self.client.get_transport())
        scp.put(function_file)
        scp.put(result_file)
        scp.put(script_file)
        
        # Execute the script on the instance
        cmd = f"python3 /tmp/covalent/{script_file}"
        _, stdout, stderr = self.client.exec_command(cmd)
        
        if stderr:
            app_log.error(stderr)
            exit(1)
        
        if stdout:
            app_log.log(stdout)    
        self.client.close()
        self.teardown()
        return (None, stdout.getvalue(), stderr.getvalue())
        

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