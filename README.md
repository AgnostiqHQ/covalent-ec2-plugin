&nbsp;

<div align="center">

<img src="https://github.com/AgnostiqHQ/covalent-ec2-plugin/blob/main/assets/ec2_readme_banner.jpg" width=150%>

</div>

## Covalent EC2 Executor Plugin

Covalent is a Pythonic workflow tool used to execute tasks on advanced computing hardware.
This executor plugin interfaces Covalent with an EC2 instance over SSH. This plugin is appropriate for executing workflow tasks on an instance that has been auto-provisioned and configured by the plugin. 

## Installation

To use this plugin with Covalent, simply install it using `pip`:

``` 
pip install covalent-ec2-plugin
```

## Configuration

The following shows an example of how a user might modify their Covalent [configuration](https://covalent.readthedocs.io/en/latest/how_to/config/customization.html) to support this plugin:

```
[executors.ec2]
ssh_key_file = "~/.ssh/ec2_key.pem"
key_name= "ec2_key"
instance_type = "t2.micro"
volume_size = "8"
ami = "amzn-ami-hvm-*-x86_64-gp2"
vpc = ""
subnet = ""
profile = "default"
credentials_file = "~/.aws/credentials"
```
This setup assumes the user has created a private key file at the location `~/.ssh/ec2_key.pem` for connecting to the instance via SSH. The setup also assumes that the user uses the `default` AWS profile and credentials file located at `~/.aws/credentials` to authenticate to their AWS account.


## Workflow Construction

Within a workflow, users can decorate electrons using the default settings:

```
import covalent as ct

@ct.electron(executor="ec2")
def my_task():
    import socket
    return socket.get_hostname()

```

or use a class object specified with a custom AWS profile within particular tasks:

```
executor = ct.executor.EC2Executor(
    ssh_key_file="~/.ssh/ec2_key.pem",
    key_name="ec2_key",
    instance_type="t2.micro",
    volume_size="8",
    ami="amzn-ami-hvm-*-x86_64-gp2",
    vpc="",
    subnet="",
    profile="custom_profile",
    credentials_file="~/.aws/credentials"
)

@ct.electron(executor=executor)
def my_custom_task(x, y):
    return x + y  
```

For more information on how to get started with Covalent, check out the project [homepage](https://github.com/AgnostiqHQ/covalent) and the official [documentation](https://covalent.readthedocs.io/en/latest/).

## Release Notes

Release notes are available in the [Changelog](https://github.com/AgnostiqHQ/covalent-executor-template/blob/main/CHANGELOG.md).

## Citation

Please use the following citation in any publications:

> W. J. Cunningham, S. K. Radha, F. Hasan, J. Kanem, S. W. Neagle, and S. Sanand.
> *Covalent.* Zenodo, 2022. https://doi.org/10.5281/zenodo.5903364

## License

Covalent is licensed under the GNU Affero GPL 3.0 License. Covalent may be distributed under other licenses upon request. See the [LICENSE](https://github.com/AgnostiqHQ/covalent-executor-template/blob/main/LICENSE) file or contact the [support team](mailto:support@agnostiq.ai) for more details.
