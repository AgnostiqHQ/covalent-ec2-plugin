import sys
import covalent as ct
from tests.create_executor import executor as ec2_exec
from numpy.random import permutation
from sklearn import svm, datasets

sklearn_install = "/home/ubuntu/miniconda3/envs/covalent-dev/bin/python -m pip install sklearn"
numpy_install = "/home/ubuntu/miniconda3/envs/covalent-dev/bin/python -m pip install numpy==1.22.4"

@ct.electron
def load_data():
    iris = datasets.load_iris()
    perm = permutation(iris.target.size)
    iris.data = iris.data[perm]
    iris.target = iris.target[perm]
    return iris.data, iris.target

@ct.electron(
    executor=ec2_exec, 
    deps_bash=ct.DepsBash(commands=[f"{sklearn_install}"])
)
def train_svm(data, C, gamma):
    X, y = data
    clf = svm.SVC(C=C, gamma=gamma)
    clf.fit(X[90:], y[90:])
    return clf

@ct.electron
def score_svm(data, clf):
    X_test, y_test = data
    return clf.score(
    	X_test[:90],
	y_test[:90]
    )

@ct.lattice
def run_experiment(C=1.0, gamma=0.7):
    data = load_data()
    clf = train_svm(
    	data=data,
	C=C,
	gamma=gamma
    )
    score = score_svm(
    	data=data,
	clf=clf
    )
    return score

dispatchable_func = ct.dispatch(run_experiment)

dispatch_id = dispatchable_func(
    	C=1.0,
    	gamma=0.7
    )
result = ct.get_result(dispatch_id=dispatch_id, wait=True)
status = str(result.status)

print(result)

if status == str(ct.status.FAILED):
    sys.exit(1)
