&nbsp;

<div align="center">

<img src="https://github.com/AgnostiqHQ/covalent-ec2-plugin/blob/main/assets/ec2_readme_banner.jpg" width=150%>

</div>

## Covalent EC2 Executor Plugin

Covalent is a Pythonic workflow tool used to execute tasks on advanced computing hardware.

This plugin allows tasks to be executed in an AWS EC2 instance (which is auto-created) when you execute your workflow with covalent.


## 1. Installation

To use this plugin with Covalent, simply install it using `pip`:

```
pip install covalent-ec2-plugin
```

## 2. Usage Example

This is a toy example of how a workflow can be adapted to utilize the EC2 Executor. Here we train a Support Vector Machine (SVM) and spin up an EC2 automatically to execute the `train_svm` electron. We also note we require [DepsPip](https://covalent.readthedocs.io/en/latest/concepts/concepts.html#depspip) to install the dependencies on the EC2 instance.

```python
from numpy.random import permutation
from sklearn import svm, datasets
import covalent as ct

deps_pip = ct.DepsPip(
	packages=["numpy==1.23.2", "scikit-learn==1.1.2"]
)

executor = ct.executor.EC2Executor(
	instance_type="t2.micro",
	volume_size=8, #GiB
	ssh_key_file="~/.ssh/id_rsa",
	key_name="key_name" # EC2 Key Pair
)

# Use executor plugin to train our SVM model.
@ct.electron(
    executor=executor,
    deps_pip=deps_pip
)
def train_svm(data, C, gamma):
    X, y = data
    clf = svm.SVC(C=C, gamma=gamma)
    clf.fit(X[90:], y[90:])
    return clf

@ct.electron
def load_data():
    iris = datasets.load_iris()
    perm = permutation(iris.target.size)
    iris.data = iris.data[perm]
    iris.target = iris.target[perm]
    return iris.data, iris.target

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

# Dispatch the workflow
dispatch_id = ct.dispatch(run_experiment)(
	C=1.0,
	gamma=0.7
)

# Wait for our result and get result value
result = ct.get_result(dispatch_id=dispatch_id, wait=True).result

print(result)
```

During the execution of the workflow one can navigate to the UI to see the status of the workflow, once completed however the above script should also output a value with the score of our model.

```
0.8666666666666667
```


## 3. Configuration

There are many configuration options that can be passed in to the class `ct.executor.EC2Executor` or by modifying the [covalent config file](https://covalent.readthedocs.io/en/latest/how_to/config/customization.html) under the section `[executors.ec2]`

For more information about all of the possible configuration values visit our [read the docs (RTD) guide](https://covalent.readthedocs.io/en/latest/api/executors/awsec2.html) for this plugin.

## 4. Required AWS Resources

In order to run your workflows with covalent there are a few notable resources that need to be provisioned first.

For more information regarding which cloud resources need to be provisioned visit our [read the docs (RTD) guide](https://covalent.readthedocs.io/en/latest/api/executors/awsec2.html) for this plugin.


The required resources include an EC2 Key Pair (which corresponds to the `key_name` config value), and optionally a VPC & Subnet that can be used instead of the EC2 executor automatically creating it.


## Getting Started with Covalent


For more information on how to get started with Covalent, check out the project [homepage](https://github.com/AgnostiqHQ/covalent) and the official [documentation](https://covalent.readthedocs.io/en/latest/).

## Release Notes

Release notes for this plugin are available in the [Changelog](https://github.com/AgnostiqHQ/covalent-ec2-plugin/blob/main/CHANGELOG.md).

## Citation

Please use the following citation in any publications:

> W. J. Cunningham, S. K. Radha, F. Hasan, J. Kanem, S. W. Neagle, and S. Sanand.
> *Covalent.* Zenodo, 2022. https://doi.org/10.5281/zenodo.5903364

## License

Covalent is licensed under the GNU Affero GPL 3.0 License. Covalent may be distributed under other licenses upon request. See the [LICENSE](https://github.com/AgnostiqHQ/covalent-executor-template/blob/main/LICENSE) file or contact the [support team](mailto:support@agnostiq.ai) for more details.
