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
    "key_file, credentials, return_value, exception",
    [(MOCK_SSH_KEY_FILE, MOCK_CREDENTIALS, True, None)],
)
@pytest.mark.asyncio
async def test_valid_credentials(key_file, credentials, return_value, exception):
    """Test valid key and credentials files."""

    mock_exec = ct.executor.EC2Executor(
        profile=MOCK_PROFILE, key_name=key_file, credentials_file=credentials
    )

    valid_res = await mock_exec._validate_credentials()
    assert valid_res == return_value


@pytest.mark.parametrize(
    "key_file, credentials, return_value, exception",
    [
        (
            "non_existent_key",
            MOCK_CREDENTIALS,
            None,
            "The instance key file 'non_existent_key' does not exist.",
        ),
        (
            MOCK_SSH_KEY_FILE,
            "non_existent_creds",
            None,
            "The AWS credentials file 'non_existent_creds' does not exist.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_invalid_credentials(key_file, credentials, return_value, exception):
    """Test that the right exceptions are raised if key or credentials files are not found"""

    mock_exec = ct.executor.EC2Executor(
        profile=MOCK_PROFILE, key_name=key_file, credentials_file=credentials
    )

    with pytest.raises(FileNotFoundError) as re:
        res = await mock_exec._validate_credentials()
        assert res is None
    assert str(re.value) == exception


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
