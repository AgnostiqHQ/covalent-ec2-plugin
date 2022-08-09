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
from socket import setdefaulttimeout
import subprocess
from multiprocessing import Queue as MPQ
from time import sleep
from typing import Any, Callable, Dict, List, Tuple

import boto3
import cloudpickle as pickle
import paramiko

# Covalent imports
from covalent._results_manager.result import Result
from covalent._shared_files import logger
from covalent_ssh_plugin.ssh import SSHExecutor
from scp import SCPClient

app_log = logger.app_log
log_stack_info = logger.log_stack_info

# The plugin class name must be given by the EXECUTOR_PLUGIN_NAME attribute. In case this
# module has more than one class defined, this lets Covalent know which is the executor class.
executor_plugin_name = "EC2Executor"

_EXECUTOR_PLUGIN_DEFAULTS = {
    "username": "ubuntu",
    "key_file": "",
    "instance_type": "t2.micro",
    "volume_size": "8GiB",
    "ami": "amzn-ami-hvm-*-x86_64-gp2",
    "vpc": "",
    "subnet": "",
    "profile": os.environ.get("AWS_PROFILE") or "default",
    "credentials_file": os.path.join(os.environ["HOME"], ".aws/credentials"),
    "cache_dir": os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(os.environ["HOME"], ".cache"), "covalent"
    ),
}


class EC2Executor(SSHExecutor):
    """
    Executor class that invokes the input function on an EC2 instance
    Args:
        username: username used to authenticate to the instance.
        profile: The name of the AWS profile
        credentials_file: Filename of the credentials file used for authentication to AWS.
        key_file: Filename of the private key used for authentication with the remote server if it exists.
        run_local_on_ec2_fail: If True, and the execution fails to run on the instance,
            then the execution is run on the local machine.
        _TF_DIR: The directory containing Terraform configuration files
        kwargs: Key-word arguments to be passed to the parent class (SSHExecutor)
    """
    _TF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "infra"))

    def __init__(
        self,
        profile: str,
        credentials_file: str,
        key_file: str,
        instance_type: str = "",
        volume_size: str = "",
        ami: str = "",
        vpc: str = "",
        subnet: str = "",
        username: str = "ubuntu",
        hostname: str = "",
        remote_home_dir: str = "/home/ubuntu",
        **kwargs,
    ) -> None:
        self.username = username
        self.hostname = hostname
        self.instance_type = instance_type,
        self.volume_size = volume_size,
        self.ami = ami,
        self.vpc = vpc,
        self.subnet = subnet,
        self.remote_home_dir = remote_home_dir
        self.profile = profile
        self.credentials_file = credentials_file
        self.key_file = key_file
        self.kwargs = kwargs
        super().__init__(username, hostname, **kwargs)

    def setup(self) -> None:
        """
        Invokes Terraform to provision supporting resources for the instance

        """
        try:
            subprocess.run(["terraform", "init"], cwd=self._TF_DIR)
            subprocess.run(["terraform", "apply", "-auto-approve=true", "-lock=false"], cwd=self._TF_DIR)

        except subprocess.SubprocessError as se:
            app_log.debug("Failed to deploy infrastructure")
            app_log.error(se)

    def teardown(self) -> None:
        """
        Invokes Terraform to terminate the instance and teardown supporting resources
        """
        try:
            subprocess.run(["terraform", "destroy", "-auto-approve=true", "-lock=false"], cwd=self._TF_DIR)

        except subprocess.SubprocessError as se:
            app_log.debug("Failed to destroy infrastructure")
            app_log.error(se)

    def get_hostname(self) -> None:
        """
        Resolves the hostname of the instance

        """

        if not self.hostname:
            client = boto3.Session(profile_name=self.profile).client("ec2")
            ec2_client = client.describe_instances()
            key_name = self.key_file.split("/")[-1].split(".")[0]

            for instances in ec2_client["Reservations"]:
                for instance in instances["Instances"]:
                    if instance["KeyName"] == key_name and instance["State"]["Name"] == "running":
                        self.hostname = instance["PublicDnsName"]

    def _client_connect(self) -> bool:
        """
        Helper function for connecting to the instance through the paramiko module.

        Args:
            None

        Returns:
            True if connection to the instance was successful, False otherwise.
        """

        self.get_hostname()

        ssh_success = False
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        if self.key_file:
            try:
                self.client.connect(
                    hostname=self.hostname, username=self.username, key_filename=self.key_file
                )

                ssh_success = True
            except Exception as e:
                app_log.error(e)

        else:
            message = "no SSH key file found. Cannot connect to host."
            app_log.error(message)

        return ssh_success

    async def run(self, function: Callable, args: List, kwargs: Dict, task_metadata: Dict) -> Any:
        """
        Invokes setup() and teardown() hooks and executes the workflow function on the instance

        """

        try:
            self.setup()
        except Exception as e:
            app_log.debug("Infrastructure deployment failed")
            app_log.error(e)

        try:
            self.run_func(function=function, args=args, kwargs=kwargs, task_metadata=task_metadata)
        except Exception as e:
            app_log.warning(f"Failed to run function {function}")
            app_log.error(e)

    def run_func(self, function: Callable, args: list, kwargs: dict, task_metadata: Dict) -> Any:
        """
        Runs the workflow function on the instance and returns the result.

        Args:
            function: Function to be run on the remote machine.
            args: Positional arguments to be passed to the function.
            kwargs: Keyword argument to be passed to the function.

        Returns:
            The result of the executed function.
        """

        dispatch_id = task_metadata["dispatch_id"]
        node_id = task_metadata["node_id"]
        operation_id = f"{dispatch_id}_{node_id}"

        exception = None

        ssh_success = self._client_connect()
        
        
        app_log.warning("Status of connection:", ssh_success)

        if not ssh_success:
            message = f"Could not connect to host '{self.hostname}' as user '{self.username}'"
        
        
        message = f"Executing node {node_id} on host {self.hostname}."
        app_log.warning(message)
        

        if self.python3_path == "":
            cmd = "which python3"
            self._client_connect()
            client_in, client_out, client_err = self.client.exec_command(cmd)
            exit_status = client_out.channel.recv_exit_status()
            cmd_output = client_out.read().decode("utf-8").strip()
            if "python3" in cmd_output:
                message = f"Python 3 is installed on host machine {self.hostname} at {cmd_output}"
                app_log.warning(message)
            else:
                message = f"No Python 3 installation found on host machine {self.hostname}"
                app_log.error(message)
                
        
        # Activate Conda env
        cmd = "source /home/ubuntu/miniconda3/bin/activate covalent"
        
        self._client_connect()
        client_in, client_out, client_err = self.client.exec_command(cmd)
        exit_status = client_out.channel.recv_exit_status()
        cmd_output = client_out.read().decode("utf-8").strip()
        if str(exit_status) == "0":
            app_log.warning(f"Conda activated successfully with {exit_status}")
        else:
            message = f"Conda activation failed on {self.hostname} with {exit_status}"
            app_log.error(message)
        
        cmd = f"mkdir -p {self.remote_cache_dir}"

        try:
            result = self.client.exec_command(cmd)

        except Exception as e:
            app_log.error(e)

        # Pickle and save location of the function and its arguments:
        (
            function_file,
            script_file,
            remote_function_file,
            remote_script_file,
            remote_result_file,
        ) = self._write_function_files(operation_id, function, args, kwargs)

        scp = SCPClient(self.client.get_transport())
        scp.put(function_file, remote_function_file)
        scp.put(script_file, remote_script_file)

        # Run the function:
        try:
            cmd = f"/home/ubuntu/miniconda3/envs/covalent/bin/python3 {remote_script_file}"
            self._client_connect()
            stdin, stdout, stderr = self.client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                app_log.warning(f"Execution of {remote_script_file} was completed")
            else:
                app_log.error(
                    f"Failed to execute {remote_script_file} on host {self.hostname} with exit status {exit_status}"
                )
        except Exception as e:
            app_log.error(e)

        # # Check that a result file was produced:
        # cmd = f"ls {remote_result_file}"
        # stdin, stdout, stderr = self.client.exec_command(cmd)
        # exit_status = stdout.channel.recv_exit_status()
        # cmd_output = stdout.read().decode("utf-8")[-1].strip()
        # app_log.warning(f'Output of looking for result file {cmd_output}')
        # if cmd_output != remote_result_file[-1].strip():
        #     message = (
        #         f"Result file {remote_result_file} on remote host {self.hostname} was not found"
        #     )
            
        #     return self._on_ssh_fail(function, args, kwargs, message)
        # else:
        #     message = (
        #         f"Result file {remote_result_file} was found on host {self.hostname} in the directory {cmd_output}"
        #     )
        #     app_log.warning(f"Path to remote result file is {remote_result_file}")
            

        # scp the pickled result to the local machine here:
        result_file = os.path.join(self.cache_dir, f"result_{operation_id}.pkl")
        scp.get(remote_result_file, result_file)
        app_log.warning(f"Location of Result file is {result_file}")

        # Load the result file:
        with open(result_file, "rb") as f_in:
            result, exception = pickle.load(f_in)

        if exception is not None:
            app_log.debug(f"exception: {exception}")
            raise exception

        self.client.close()
        return result

    def _write_function_files(
        self,
        operation_id: str,
        fn: Callable,
        args: list,
        kwargs: dict,
    ) -> Tuple:
        """
        Helper function to pickle the function to be executed to file, and write the
            python script which calls the function.

        Args:
            operation_id: A concatenation of the dispatch ID and task ID.
            fn: The input python function which will be executed and whose result
                is ultimately returned by this function.
            args: List of positional arguments to be used by the function.
            kwargs: Dictionary of keyword arguments to be used by the function.
        """

        # Pickle and save location of the function and its arguments:
        function_file = os.path.join(self.cache_dir, f"function_{operation_id}.pkl")

        with open(function_file, "wb") as f_out:
            pickle.dump((fn, args, kwargs), f_out)

        remote_function_file = os.path.join(
            self.remote_home_dir, self.remote_cache_dir, f"function_{operation_id}.pkl"
        )

        # Write the code that the instance will use to execute the function.

        message = f"Function file names:\nLocal function file: {function_file}\n"
        message += f"Remote function file: {remote_function_file}"
        app_log.warning(message)

        remote_result_file = os.path.join(
            self.remote_home_dir, self.remote_cache_dir, f"result_{operation_id}.pkl"
        )
        exec_script = "\n".join(
            [
                "import sys",
                "",
                "result = None",
                "exception = None",
                "",
                "",
                "try:",
                "    import cloudpickle as pickle",
                "except Exception as e:",
                "    import pickle",
                f"    with open('{remote_result_file}','wb') as f_out:",
                "        pickle.dump((None, e), f_out)",
                "        exit()",
                "",
                f"with open('{remote_function_file}', 'rb') as f_in:",
                "    fn, args, kwargs = pickle.load(f_in)",
                "    try:",
                "        result = fn(*args, **kwargs)",
                "    except Exception as e:",
                "        exception = e",
                "",
                f"with open('{remote_result_file}','wb') as f_out:",
                "    pickle.dump((result, exception), f_out)",
                "",
            ]
        )
        script_file = os.path.join(self.cache_dir, f"exec_{operation_id}.py")
        remote_script_file = os.path.join(self.remote_cache_dir, f"exec_{operation_id}.py")
        with open(script_file, "w") as f_out:
            f_out.write(exec_script)

        return (
            function_file,
            script_file,
            remote_function_file,
            remote_script_file,
            remote_result_file,
        )
