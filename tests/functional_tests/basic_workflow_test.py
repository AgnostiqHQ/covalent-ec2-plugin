import sys
import covalent as ct
from tests.create_executor import executor as ec2_exec


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
status = str(ct.get_result(dispatch_id=dispatch_id, wait=True).status)

if status == str(ct.status.FAILED):
    sys.exit(1)