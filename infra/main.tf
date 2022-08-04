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


################################################################################
# Supporting Resources
################################################################################

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name = "name"
    values = ["ubuntu-minimal/images/hvm-ssd/ubuntu-focal-20.04-amd64-minimal-*"]
  }

  owners = ["099720109477"]
}


resource "aws_s3_bucket" "s3_bucket" {
  bucket_prefix = var.aws_s3_bucket == "" ? var.name : ""
  count         = var.aws_s3_bucket == "" ? 1 : 0
}

################################################################################
# EC2 Module
################################################################################

module "ec2_instance" {
  source = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 3.0"

  name = var.name
  ami = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.covalent_firewall.id]
  subnet_id = "${var.vpc_id == "" ? module.vpc.public_subnets[0] : var.subnet_id}"
  associate_public_ip_address = true

  key_name = ""
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
  monitoring = true

  root_block_device = [{
    volume_type = "gp2"
    volume_size = var.disk_size
  }]

  user_data = <<EOF
  #!/bin/bash
  cd ~
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
  bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda
  rm Miniconda3-latest-Linux-x86_64.sh
  echo 'export PATH="~/miniconda/bin:$PATH"' >> ~/.bashrc 
  source .bashrc
  conda update conda -y
  conda init bash
  source .bashrc
  conda create -n covalent python=3.8 -y
  conda activate covalent
  pip install cloudpickle
  pip install botocore
  pip install boto3
  pip install --pre covalent
  alembic init covalent_migrations/
  covalent start
    )
  EOF
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2_profile"
  role = aws_iam_role.covalent_iam_role.name
}


