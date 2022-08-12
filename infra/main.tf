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

provider "aws" {
    profile = "default"
    region = var.aws_region
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name = "name"
    values = ["ubuntu-minimal/images/hvm-ssd/ubuntu-focal-20.04-amd64-minimal-*"]
  }

  owners = ["099720109477"]
}

resource "aws_iam_instance_profile" "ec2" {
  name = "ec2"
  role = aws_iam_role.covalent_iam_role.name
}


resource "aws_instance" "covalent_svc_instance" {

  ami = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.covalent_firewall.id]
  subnet_id = "${var.vpc_id == "" ? module.vpc.public_subnets[0] : var.subnet_id}"
  associate_public_ip_address = true

  key_name = "test-pair"  # Name of a valid key file
  iam_instance_profile = aws_iam_instance_profile.ec2.name
  monitoring = true

  root_block_device {
    volume_type = "gp2"
    volume_size = var.disk_size
  }

  tags = {
    "Name" = var.name
  }

}

resource "null_resource" "deps_install" {

  provisioner "remote-exec" {

    inline = [
      "apt-get update",  # This is not allowed
      "echo 'Installing Conda'",
      "wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.12.0-Linux-x86_64.sh",
      "sh ./Miniconda3-py38_4.12.0-Linux-x86_64.sh -b -p /home/ubuntu/miniconda3",
      "rm ./Miniconda3-py38_4.12.0-Linux-x86_64.sh",
      "echo 'export PATH='/home/ubuntu/miniconda3/bin:$PATH'' >> ~/.bashrc ",
      "source ~/.bashrc",
      "/home/ubuntu/miniconda3/bin/conda init bash",
      "echo 'Installing Conda Environment'",
      "/home/ubuntu/miniconda3/bin/conda create -n covalent-dev python=3.8.13 -y",
      "echo 'Activating Covalent Environment'",
      "conda activate covalent-dev",
      "echo 'Installing Packages'",
      "conda install -p /home/ubuntu/miniconda3/envs/covalent-dev cloudpickle=2.0.0 --file requirements.txt",
      "Checking Python Path",
      "echo 'which python'",
      "/home/ubuntu/miniconda3/envs/covalent-dev/bin/pip install --pre covalent",
      "echo 'Starting Covalent'",
      "/home/ubuntu/miniconda3/bin/covalent-dev/bin/covalent purge -y",
      "/home/ubuntu/miniconda3/envs/covalent-dev/bin/covalent db migrate",
      "/home/ubuntu/miniconda3/envs/covalent-dev/bin/covalent start"
    ]

  }

  connection {
    type = "ssh"
    user = "ubuntu"
    private_key = file("/home/user/.ssh/test-pair.pem") # Path to a valid key file
    host = aws_instance.covalent_svc_instance.public_ip

  }

}
