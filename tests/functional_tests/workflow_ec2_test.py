import covalent as ct

from covalent_ec2_plugin.ec2 import EC2Executor

ec2_exec = EC2Executor(
    profile="default",
    credentials_file="/Users/user/.aws/credentials",
    key_name="ssh_key",
    ssh_key_file="/Users/user/.ssh/ssh_key.pem",
    vpc="",
    subnet="",
)


@ct.electron(executor=ec2_exec)
def join_words(a, b):
    return "-".join([a, b])


@ct.electron(executor=ec2_exec)
def excitement(a):
    return f"{a}!"


@ct.lattice
def simple_workflow(a, b):
    phrase = join_words(a, b)
    return excitement(phrase)


dispatch_id = ct.dispatch(simple_workflow)("Hello", "Covalent")
result = ct.get_result(dispatch_id, wait=True)

