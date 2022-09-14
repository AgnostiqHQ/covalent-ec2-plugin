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

import pytest
import tftest

from tests.create_executor import executor as ec2_exec

MOCK_USERNAME = "mock_username"
MOCK_PROFILE = "mock_profile"
MOCK_CREDENTIALS = "/tmp/mock_credentials"
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
        dispatch_id=MOCK_DISPATCH_ID, node_id=MOCK_NODE_ID
    ),
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

    tf_file = "main.tf"
    with open(os.path.join(MOCK_TF_DIR, tf_file), "w") as temp_file:
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

    assert plan.variables["name"] == "covalent-svc"
    assert plan.variables["instance_type"] == ec2_exec.instance_type
    assert plan.variables["disk_size"] == ec2_exec.volume_size
    assert plan.variables["aws_region"] == os.getenv("AWS_REGION")
    assert plan.variables["vpc_id"] == ec2_exec.vpc
    assert plan.variables["subnet_id"] == ec2_exec.subnet


@pytest.mark.asyncio
async def test_custom_variables(mock_plan):
    """Tests whether custom variables are correctly passed to Terraform at runtime"""

    # Set custom attributes in executor instance
    ec2_exec.username = MOCK_USERNAME
    ec2_exec.profile = MOCK_PROFILE
    ec2_exec.credentials_file = MOCK_CREDENTIALS
    ec2_exec.key_name = MOCK_KEY_NAME
    ec2_exec.ssh_key_file = MOCK_SSH_KEY_FILE
    ec2_exec.instance_type = MOCK_INSTANCE_TYPE
    ec2_exec.volume_size = MOCK_DISK_SIZE
    ec2_exec.vpc = MOCK_VPC
    ec2_exec.subnet = MOCK_SUBNET

    with pytest.raises(RuntimeError) as re:
        # Expected to raise an exception in setup() since key and credentials are mocks
        await ec2_exec.setup(
            task_metadata={"dispatch_id": MOCK_DISPATCH_ID, "node_id": MOCK_NODE_ID}
        )
    msg = f"error configuring Terraform AWS Provider: failed to get shared config profile, {MOCK_PROFILE}"
    assert msg in str(re.value)

    # Check that custom variables are correctly constructed in setup()
    assert mock_plan.variables["name"] == MOCK_PLAN_VARS["name"]
    assert mock_plan.variables["aws_profile"] == ec2_exec.profile
    assert mock_plan.variables["aws_credentials"] == ec2_exec.credentials_file
    assert mock_plan.variables["instance_type"] == ec2_exec.instance_type
    assert mock_plan.variables["disk_size"] == str(ec2_exec.volume_size)
    assert mock_plan.variables["key_name"] == ec2_exec.key_name
    assert mock_plan.variables["key_file"] == ec2_exec.ssh_key_file
    assert mock_plan.variables["vpc_id"] == ec2_exec.vpc
    assert mock_plan.variables["subnet_id"] == ec2_exec.subnet

    with pytest.raises(FileNotFoundError) as fe:
        # Expected to raise an exception in teardown() since infrastructure was not created in setup()
        await ec2_exec.teardown(
            task_metadata={"dispatch_id": MOCK_DISPATCH_ID, "node_id": MOCK_NODE_ID}
        )
    mock_state_file = os.path.join(
        ec2_exec.cache_dir, f"{MOCK_DISPATCH_ID}-{MOCK_NODE_ID}.tfstate"
    )
    assert (
        str(fe.value)
        == f"Could not find Terraform state file: {mock_state_file}. Infrastructure may need to be manually deprovisioned."
    )


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
    firewall_description = plan.resources["aws_security_group.covalent_firewall"]["values"][
        "description"
    ]
    ingress_rule = plan.resources["aws_security_group.covalent_firewall"]["values"]["ingress"]
    assert instance_name == "covalent_svc_instance"
    assert firewall_name == "covalent_firewall"
    assert firewall_description == "Allow traffic to Covalent server"
    assert ingress_rule[0]["description"] == "Allow SSH Access"
    assert ingress_rule[0]["from_port"] == 22 and ingress_rule[0]["to_port"] == 22


def test_outputs(plan):
    """Tests Terraform's output after invoking setup()"""

    ec2_exec.username = "ubuntu"
    assert plan.outputs["username"] == ec2_exec.username
    assert ec2_exec.python_path in plan.outputs["python3_path"]
    assert ec2_exec.remote_cache in plan.outputs["remote_cache"]
