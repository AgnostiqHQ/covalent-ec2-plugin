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

from pathlib import Path

import covalent as ct
import pytest

from tests.unit_tests.infra_test import MOCK_PLAN_VARS

MOCK_PROFILE = MOCK_PLAN_VARS["aws_profile"]
MOCK_USERNAME = "mock_username"
MOCK_SSH_KEY_FILE = MOCK_PLAN_VARS["key_file"]
MOCK_CREDENTIALS = MOCK_PLAN_VARS["aws_credentials"]

with open(MOCK_SSH_KEY_FILE, "w") as tmp1:
    tmp1.write("@^598")

with open(MOCK_CREDENTIALS, "w") as tmp2:
    tmp2.write("[default]\naws_access_key_id = 123\naws_secret_access_key =aBc")

ec2_exec = ct.executor.EC2Executor(username=MOCK_USERNAME, profile=MOCK_PROFILE)


@pytest.mark.asyncio
async def test_cancel():
    with pytest.raises(NotImplementedError):
        await ec2_exec.cancel()


def test_init_ec2_executor():
    """Tests whether executor attributes are correctly constructed"""

    assert ec2_exec.username == MOCK_USERNAME
    assert ec2_exec.profile == MOCK_PROFILE


@pytest.mark.parametrize(
    "does_aws_credentials_exist, does_ssh_key_exist",
    [(False, False), (False, True), (True, True), (True, False)],
)
@pytest.mark.asyncio
async def test_validate_credentials(
    does_aws_credentials_exist, does_ssh_key_exist, tmp_path: Path
):
    """Test validation of key file and credentials."""

    aws_credentials_path = "/some/path/that/does/not/exist"
    ssh_key_file = "/some/path/that/does/not/exist"

    if does_aws_credentials_exist:
        aws_credentials_path = tmp_path / "aws_credentials"
        aws_credentials_path.touch()
        aws_credentials_path = str(aws_credentials_path)

    if does_ssh_key_exist:
        ssh_key_file = tmp_path / "ssh_key"
        ssh_key_file.touch()
        ssh_key_file = str(ssh_key_file)

    mock_exec = ct.executor.EC2Executor(
        profile=MOCK_PROFILE, ssh_key_file=ssh_key_file, credentials_file=aws_credentials_path
    )

    if does_aws_credentials_exist and does_ssh_key_exist:
        try:
            await mock_exec._validate_credentials()
        except:
            pytest.fail(
                "Validate credentials should not throw an error if both aws credentials & ssh key exist."
            )
    else:
        with pytest.raises(FileNotFoundError) as re:
            await mock_exec._validate_credentials()


def test_upload_task():
    pass


def test_submit_task():
    pass


def test_get_status():
    pass


def test_poll_task():
    pass


def test_query_result():
    pass
