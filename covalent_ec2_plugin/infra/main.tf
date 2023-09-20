# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the Apache License 2.0 (the "License"). A copy of the
# License may be obtained with this software package or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Use of this file is prohibited except in compliance with the License.
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

locals {
  username = "ubuntu"
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu-minimal/images/hvm-ssd/ubuntu-focal-20.04-amd64-minimal-*"]
  }

  owners = ["099720109477"]
}


resource "aws_instance" "covalent_ec2_instance" {

  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  vpc_security_group_ids      = [aws_security_group.covalent_firewall.id]
  subnet_id                   = var.vpc_id == "" ? module.vpc.public_subnets[0] : var.subnet_id
  associate_public_ip_address = true

  key_name             = var.key_name # Name of a valid key pair
  monitoring           = true

  root_block_device {
    volume_type = "gp2"
    volume_size = var.disk_size
  }

  tags = {
    "Name" = var.name
  }
}

resource "null_resource" "deps_install" {

  provisioner "file" {
    source      = "sudo-commands.sh"
    destination = "/tmp/script.sh"
  }
  provisioner "remote-exec" {
    inline = [
      "echo 'Installing Conda...'",
      "wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.12.0-Linux-x86_64.sh",
      "chmod +x Miniconda3-py38_4.12.0-Linux-x86_64.sh",
      "./Miniconda3-py38_4.12.0-Linux-x86_64.sh -b -p ~/miniconda3",
      "echo 'Creating Conda Environment...'",
      "eval \"$(~/miniconda3/bin/conda shell.bash hook)\"",
      "conda init bash",
      "conda create -n covalent python=3.8.13 -y",
      "echo \"conda activate covalent\" >> $HOME/.bashrc",
      "conda activate covalent",
      "echo 'Installing Covalent...'",

      # TODO: Update to a variable version
      "pip install covalent==${var.covalent_version}",
      "chmod +x /tmp/script.sh",
      "sudo bash /tmp/script.sh",
      "echo ok"
    ]
  }

  connection {
    type        = "ssh"
    user        = local.username
    private_key = file(var.key_file) # Path to a valid key file
    host        = aws_instance.covalent_ec2_instance.public_ip
  }
}
