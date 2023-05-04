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

# Ignore results folders

from pathlib import Path
from unittest import mock

import covalent as ct
import pytest

from covalent_ec2_plugin import ec2

MOCK_USERNAME = "ubuntu"
MOCK_PROFILE = "default"


@pytest.fixture
def executor():
    config = {"username": MOCK_USERNAME, "profile": MOCK_PROFILE}
    ec2_exec = ec2.EC2Executor(**config)
    return ec2_exec


@pytest.mark.asyncio
async def test_cancel(executor: ec2.EC2Executor):
    with pytest.raises(NotImplementedError):
        await executor.cancel()


def test_init_ec2_executor(executor):
    """Tests whether executor attributes are correctly constructed"""

    assert executor.username == MOCK_USERNAME
    assert executor.profile == MOCK_PROFILE


@pytest.mark.asyncio
async def test_teardown(executor: ec2.EC2Executor, mocker: mock, tmp_path: Path):
    mock_task_metadata = {"dispatch_id": "123", "node_id": 1}

    state_file = tmp_path / "state.tfstate"
    not_existing_state_file = tmp_path / "dne.tfstate"
    state_file.touch()

    executor.infra_vars = ["-var='mock_var=123'"]

    run_async_process_mock = mock.AsyncMock()
    mocker.patch(
        "covalent_ec2_plugin.ec2.EC2Executor._run_async_subprocess",
        side_effect=run_async_process_mock,
    )

    # test failure if tfstate does not exist
    mocker.patch(
        "covalent_ec2_plugin.ec2.EC2Executor._get_tf_statefile_path",
        return_value=str(not_existing_state_file),
    )
    with pytest.raises(FileNotFoundError):
        await executor.teardown(mock_task_metadata)

    mocker.patch(
        "covalent_ec2_plugin.ec2.EC2Executor._get_tf_statefile_path", return_value=str(state_file)
    )
    await executor.teardown(mock_task_metadata)

    run_async_process_mock.assert_called_once()


@pytest.mark.parametrize(
    "does_ssh_key_exist",
    [(False), (True)],
)
@pytest.mark.asyncio
async def test_setup(executor: ec2.EC2Executor, mocker: mock, does_ssh_key_exist, tmp_path: Path):
    """Test validation of key file and setup."""

    MOCK_TF_VAR_OUTPUT = "mocked_tf_output"

    mock_task_metadata = {"dispatch_id": "123", "node_id": 1}
    ssh_key_file = tmp_path / "ssh_key"
    executor.ssh_key_file = str(ssh_key_file)

    state_file = tmp_path / "state.tfstate"
    state_file.touch()

    boto3_mock = mocker.patch("covalent_ec2_plugin.ec2.boto3")
    subprocess_mock: mock.MagicMock = mocker.patch("covalent_ec2_plugin.ec2.subprocess")

    run_async_process_mock = mock.AsyncMock()
    get_tf_output_mock = mock.AsyncMock()
    get_tf_output_mock.return_value = MOCK_TF_VAR_OUTPUT

    mocker.patch(
        "covalent_ec2_plugin.ec2.EC2Executor._run_async_subprocess",
        side_effect=run_async_process_mock,
    )
    mocker.patch(
        "covalent_ec2_plugin.ec2.EC2Executor._get_tf_output",
        side_effect=get_tf_output_mock,
    )

    mocker.patch(
        "covalent_ec2_plugin.ec2.EC2Executor._get_tf_statefile_path", return_value=str(state_file)
    )

    if does_ssh_key_exist:
        ssh_key_file.touch()

    if does_ssh_key_exist:
        try:
            await executor.setup(mock_task_metadata)
            assert executor.username == MOCK_TF_VAR_OUTPUT
            assert executor.hostname == MOCK_TF_VAR_OUTPUT
            assert executor.remote_cache == MOCK_TF_VAR_OUTPUT
            subprocess_mock.run.assert_called_once()
            run_async_process_mock.assert_called_once()
        except FileNotFoundError:
            pytest.fail("Setup should not throw an error if the ssh key file exists.")
    else:
        ec2_client_mock = boto3_mock.Session.return_value.client.return_value
        
        mock_key_name = ec2.FALLBACK_KEYPAIR_NAME
        mock_ssh_key_file = Path(ec2.FALLBACK_SSH_HOME) / f"{mock_key_name}.pem"

        mocked_key_pair = {"KeyMaterial": "mocked_key_material"}
        ec2_client_mock.create_key_pair.return_value = mocked_key_pair

        os_chmod_mock = mocker.patch("covalent_ec2_plugin.ec2.os.chmod")

        mocker.patch("covalent_ec2_plugin.ec2.Path.exists", return_value=False)

        with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
            
            await executor.setup(mock_task_metadata)
            
            ec2_client_mock.create_key_pair.assert_called_with(KeyName=mock_key_name)

            file_handle = mocked_open()
            file_handle.write.assert_called_with(mocked_key_pair["KeyMaterial"])
        
        os_chmod_mock.assert_called_with(mock_ssh_key_file, 0o400)



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
