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
import subprocess
from unittest.mock import MagicMock
import pytest
import tftest
from tests.create_executor import init_executor

MOCK_USERNAME = "mock_username"
MOCK_PROFILE = "mock_profile"
MOCK_CREDENTIALS = "mock_credentials"
MOCK_SSH_KEY_FILE = "/tmp/mock_key.pem"
MOCK_KEY_NAME = "mock_key"
MOCK_INSTANCE_TYPE = "mock_instance_type"
MOCK_DISK_SIZE = 64
MOCK_VPC = "mock_vpc"
MOCK_SUBNET = "mock_subnet"
MOCK_DISPATCH_ID = "mock_dispatch_id"
MOCK_NODE_ID = "mock_node_id"
MOCK_TF_DIR = "/tmp"

MOCK_PLAN_VARS = {
    "aws_profile": MOCK_PROFILE,
    "aws_credentials": MOCK_CREDENTIALS,
    "key_file": MOCK_SSH_KEY_FILE,
    "key_name": MOCK_KEY_NAME,
    "vpc_id": MOCK_VPC,
    "subnet_id": MOCK_SUBNET,
    "instance_type": MOCK_INSTANCE_TYPE,
    "disk_size": MOCK_DISK_SIZE,
    "name": "covalent-task-{dispatch_id}-{node_id}".format(
        dispatch_id=MOCK_DISPATCH_ID,
        node_id=MOCK_NODE_ID
    ) 
}

@pytest.fixture
def plan():
    """Returns a Terraform plan object"""

    tf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "infra"))
    proc = subprocess.run(["terraform", "init"], cwd=tf_dir, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8").strip())

    tf = tftest.TerraformTest(tf_dir)
    return tf.plan(output=True)

@pytest.fixture
def mock_plan():
    """Returns a mock Terraform plan object for testing custom variables"""
    
    tf_file = 'main.tf'
    with open(os.path.join('/tmp', tf_file), 'w') as temp_file:
        temp_file.write(
            """provider "aws" { \n\tprofile = "" \n\tregion = ""\n} 
               \nvariable "name" {\n\tdefault = "" \n}
               \nvariable "aws_credentials" {\n\tdefault = "" \n}
               \nvariable "aws_profile" {\n\tdefault = "" \n}
               \nvariable "key_name" {\n\tdefault = "" \n}
               \nvariable "key_file" {\n\tdefault = "" \n}
               \nvariable "instance_type" {\n\tdefault = "" \n}
               \nvariable "disk_size" {\n\tdefault = 8 \n\ttype = number \n}
               \nvariable "vpc_id" {\n\tdefault = "" \n}
               \nvariable "subnet_id" {\n\tdefault = "" \n}
            """
            )
    proc = subprocess.run(["terraform", "init"], cwd=MOCK_TF_DIR, capture_output=True) 
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8").strip())

    tf = tftest.TerraformTest(MOCK_TF_DIR)
    return tf.plan(output=True, tf_vars=MOCK_PLAN_VARS)


def test_default_variables(plan):
    """Test default variables"""

    exec_obj = init_executor()
    assert plan.variables['name'] == 'covalent-svc'
    assert plan.variables['key_name'] == ""
    assert plan.variables['key_file'] == ""
    assert plan.variables['instance_type'] == exec_obj.instance_type
    assert plan.variables['disk_size'] == exec_obj.volume_size
    assert plan.variables['aws_region'] == os.environ.get('AWS_REGION')
    assert plan.variables['vpc_id'] == exec_obj.vpc
    assert plan.variables['subnet_id'] == exec_obj.subnet
    

@pytest.mark.asyncio
async def test_custom_variables(plan, mock_plan):
    """Tests whether custom variables are correctly passed to Terraform at runtime"""

    exec_obj = init_executor()
    exec_obj.username = MOCK_USERNAME
    exec_obj.profile = MOCK_PROFILE
    exec_obj.credentials_file = MOCK_CREDENTIALS
    exec_obj.key_name = MOCK_KEY_NAME
    exec_obj.ssh_key_file = MOCK_SSH_KEY_FILE
    exec_obj.instance_type = MOCK_INSTANCE_TYPE
    exec_obj.volume_size = MOCK_DISK_SIZE
    exec_obj.vpc = MOCK_VPC
    exec_obj.subnet = MOCK_SUBNET
    
    # Check that custom variables are correctly parsed in setup()
    try:
        await exec_obj.setup(task_metadata={"dispatch_id": MOCK_DISPATCH_ID, "node_id": MOCK_NODE_ID})
    except Exception as e:
        # Expected to fail when provisioning resources since the key and credentials are mocks
        pass
    
    assert mock_plan.variables["name"] == MOCK_PLAN_VARS["name"]
    assert mock_plan.variables['aws_profile'] == exec_obj.profile
    assert mock_plan.variables['aws_credentials'] == exec_obj.credentials_file
    assert mock_plan.variables['instance_type'] == exec_obj.instance_type
    assert mock_plan.variables['disk_size'] == str(exec_obj.volume_size)
    assert mock_plan.variables['key_name'] == exec_obj.key_name
    assert mock_plan.variables['key_file'] == exec_obj.ssh_key_file
    assert mock_plan.variables['vpc_id'] == exec_obj.vpc
    assert mock_plan.variables['subnet_id'] == exec_obj.subnet
    
    try:
        await exec_obj.teardown(task_metadata={"dispatch_id": MOCK_DISPATCH_ID, "node_id": MOCK_NODE_ID})
    except Exception as e:
        # Expected to fail since infrastructure was never created
        assert type(e) == FileNotFoundError
        
def test_modules(plan):
    """Tests module specifications"""
    
    vpc_mod = plan.modules["module.vpc"]
    vpc_name = vpc_mod.resources["aws_vpc.this[0]"]["values"]["tags"]["Name"]
    vpc_cidr_block = vpc_mod.resources["aws_vpc.this[0]"]["values"]["cidr_block"]
    assert vpc_name == "covalent-svc-vpc"
    assert vpc_cidr_block == "10.0.0.0/24"


def test_resources(plan):
    """Tests resource specifications"""

    instance_name = plan.resources["aws_instance.covalent_svc_instance"]["name"]
    firewall_name = plan.resources["aws_security_group.covalent_firewall"]["name"]
    firewall_description = plan.resources["aws_security_group.covalent_firewall"]["values"]["description"]
    ingress_rule = plan.resources["aws_security_group.covalent_firewall"]["values"]["ingress"]
    assert instance_name == 'covalent_svc_instance'
    assert firewall_name == "covalent_firewall"
    assert firewall_description == "Allow traffic to Covalent server"
    assert ingress_rule[0]["description"] == "Allow SSH Access"
    assert ingress_rule[0]["from_port"] == 22 and ingress_rule[0]["to_port"] == 22


def test_outputs(plan):
    """Tests Terraform's output after invoking setup()"""

    exec_obj = init_executor()
    exec_obj.username = "ubuntu"
    assert plan.outputs["username"] == exec_obj.username
    assert exec_obj.python_path in plan.outputs["python3_path"]
    assert exec_obj.remote_cache_dir in plan.outputs["remote_cache_dir"]
