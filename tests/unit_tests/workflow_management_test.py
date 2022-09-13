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

import pytest
import covalent as ct
from tests.unit_tests.infra_test import MOCK_PLAN_VARS


@pytest.mark.asyncio
async def test_init_ec2_executor():
    """Tests whether executor attributes are correctly constructed"""

    # Set mock custom attributes in executor instance
    MOCK_PROFILE = MOCK_PLAN_VARS["aws_profile"]
    MOCK_USERNAME = "mock_username"
    ec2_exec = ct.executor.EC2Executor(username=MOCK_USERNAME, profile=MOCK_PROFILE)

    assert ec2_exec.username == MOCK_USERNAME
    assert ec2_exec.profile == MOCK_PROFILE


@pytest.mark.asyncio
async def test_upload_task():

    pass


@pytest.mark.asyncio
def test_submit_task():

    pass


@pytest.mark.asyncio
def test_get_status():
    pass


@pytest.mark.asyncio
def test_poll_task():

    pass


@pytest.mark.asyncio
def test_query_result():

    pass


@pytest.mark.asyncio
def test_cancel():

    pass