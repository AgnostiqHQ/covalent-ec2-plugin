import covalent as ct
import pytest


@pytest.mark.functional_tests
def test_basic_workflow():
    @ct.electron(executor="ec2")
    def join_words(a, b):
        return "-".join([a, b])

    @ct.electron
    def excitement(a):
        return f"{a}!"

    @ct.lattice
    def simple_workflow(a, b):
        phrase = join_words(a, b)
        return excitement(phrase)

    dispatch_id = ct.dispatch(simple_workflow)("Hello", "Covalent")
    result = ct.get_result(dispatch_id=dispatch_id, wait=True)
    status = str(result.status)

    print(result)

    assert status == str(ct.status.COMPLETED)
