import covalent as ct

from covalent_ec2_plugin.ec2 import EC2Executor

ec2_exec = EC2Executor(
    profile="default",
    credentials_file="~/.aws/credentials_sankalp",
    key_name="sankalp_key_pair",
    ssh_key_file="/Users/sankalpsanand/.aws/sankalp_key_pair.pem",
    vpc="vpc-07bdd9ca40c4c50a7",
    subnet="subnet-0a0a7f2a7532383c3",
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
print(dispatch_id)

# result = ct.get_result(dispatch_id, wait=True)

