import boto3
import time
import asyncio
from botocore.exceptions import ClientError
from covalent._shared_files.logger import app_log
import urllib.request


def assert_security_group_exists(
    group_name: str, vpc_id: str, group_description: str, group_id: str = ""
) -> bool:
    """Return True if group exists else False"""
    ec2_client = boto3.client("ec2")
    try:
        response = ec2_client.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [group_name]},
                {"Name": "vpc-id", "Values": [vpc_id]},
                {"Name": "description", "Values": [group_description]},
                {"Name": "group-id", "Values": [group_id]} if group_id else {},
            ]
        )
        if response["SecurityGroups"]:
            group_id = response["SecurityGroups"][0]["GroupId"]
            app_log.debug(f"Security group {group_name}/{group_id} exists")
            return True
        else:
            app_log.debug(f"Security group {group_name} not found in VPC {vpc_id}")
            return False
    except ClientError as error:
        app_log.error(error)
        raise


def create_security_group_sync(group_name: str, vpc_id: str, group_description: str) -> str:
    """Create a security group if it does not exists"""

    if assert_security_group_exists(
        group_name=group_name, vpc_id=vpc_id, group_description=group_description
    ):
        return ""

    my_ip = urllib.request.urlopen("https://v4.ident.me/").read().decode("utf8")
    ec2_client = boto3.client("ec2")

    try:
        response = ec2_client.create_security_group(
            GroupName=group_name, VpcId=vpc_id, Description=group_description
        )

        # Authorize ingress rule from `my_ip`
        ec2_client.authorize_security_group_ingress(
            CidrIp=f"{my_ip}/32",
            FromPort=22,
            ToPort=22,
            IpProtocol="tcp",
            GroupId=response["GroupId"],
        )
        return response["GroupId"]
    except ClientError as error:
        app_log.error(error)
        raise


async def create_security_group_async(group_name: str, vpc_id: str, group_description: str) -> str:
    """Create the security group in a non-blocking manner"""
    loop = asyncio.get_running_loop()
    fut = loop.run_in_executor(
        None, create_security_group_sync, group_name, vpc_id, group_description
    )
    return await fut


def delete_security_group_sync(
    group_name: str,
    vpc_id: str,
    group_description: str,
    group_id: str = "",
    timeout: int = 30,
    poll_freq: int = 1,
) -> None:
    """Delete security group while avoiding any DependencyViolation errors"""
    ec2_client = boto3.client("ec2")

    if not assert_security_group_exists(
        group_name=group_name,
        vpc_id=vpc_id,
        group_description=group_description,
        group_id=group_id,
    ):
        return

    time_left = timeout
    while time_left > 0:
        time.sleep(poll_freq)
        try:
            app_log.debug(f"Deleting security group {group_name}/{group_id} from VPC {vpc_id}")
            ec2_client.delete_security_group(GroupId=group_id, GroupName=group_name)
            app_log.debug(f"Security group {group_name}/{group_id} successfully deleted")
        except ClientError as error:
            if error.response["Error"]["Code"] == "DependencyViolation":
                app_log.debug(str(error))
            else:
                break
        time_left -= poll_freq


async def delete_security_group_async(
    group_name: str,
    vpc_id: str,
    group_description: str,
    group_id: str = "",
    timeout: int = 30,
    poll_freq: int = 1,
):
    """Delete security group in a non-blocking manner"""
    loop = asyncio.get_running_loop()
    fut = loop.run_in_executor(
        None,
        delete_security_group_sync,
        group_name,
        vpc_id,
        group_description,
        group_id,
        timeout,
        poll_freq,
    )
    return await fut
