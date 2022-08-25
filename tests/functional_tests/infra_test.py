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
from create_executor import init_executor


@pytest.fixture
def plan():
    """Returns a Terraform plan object"""

    tf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "infra"))
    proc = subprocess.run(["terraform", "init"], cwd=tf_dir, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8").strip())

    tf = tftest.TerraformTest(tf_dir)
    return tf.plan(output=True)


def test_default_variables(plan):
    """Tests default variables"""

    exec_obj = init_executor()
    assert plan.variables['name'] == 'covalent-svc'
    assert plan.variables['key_name'] == ""
    assert plan.variables['key_file'] == ""
    assert plan.variables['instance_type'] == exec_obj.instance_type
    assert plan.variables['disk_size'] == exec_obj.volume_size
    assert plan.variables['aws_region'] == os.environ.get('AWS_REGION')
    assert plan.variables['vpc_id'] == exec_obj.vpc
    assert plan.variables['subnet_id'] == exec_obj.subnet


@pytest.mark.skip('Mock infra setup and credentials')
@pytest.mark.asyncio
async def test_custom_variables(plan):
    """Tests whether custom variables are correctly passed to Terraform after invoking setup()"""

    exec_obj = init_executor()
    exec_obj.profile = 'custom_profile'
    exec_obj.key_name = 'custom_key'
    exec_obj.ssh_key_file = '/tmp/custom_key.pem'
    exec_obj.instance_type = "t2.large"
    exec_obj.vpc = 'custom_vpc_id'
    exec_obj.subnet = 'custom_subnet_id'

    try:
        await exec_obj.setup(task_metadata={"dispatch_id": "test-dispatch", "node_id": "0"})
    except Exception as e:
        raise pytest.exit(f"Terraform failed to create the required resources and raised an error {e}")

    assert plan.variables['aws_profile'] == exec_obj.profile
    assert plan.variables['aws_credentials'] == exec_obj.credentials_file
    assert plan.variables['ssh_key_file'] == exec_obj.ssh_key_file

    try:
        await exec_obj.teardown(task_metadata={"dispatch_id": "test-dispatch", "node_id": "0"})
    except Exception as e:
        raise pytest.exit(f"Terraform failed to destroy the provisioned resources and raised an error {e}")


def test_modules(plan):
    "Tests module specifications"
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
