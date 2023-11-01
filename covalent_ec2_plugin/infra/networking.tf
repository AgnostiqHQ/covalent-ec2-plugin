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

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  create_vpc = (var.vpc_id == "")

  name = "${var.name}-vpc"
  cidr = var.vpc_cidr

  azs = ["${var.aws_region}a"]

  public_subnets = [
    cidrsubnet(var.vpc_cidr, 0, 0)
  ]
  private_subnets = []

  enable_nat_gateway   = false
  single_nat_gateway   = false
  enable_dns_hostnames = true
  map_public_ip_on_launch = true
}

data "http" "myip" {
  url = "https://ipv4.icanhazip.com"
}

resource "aws_security_group" "covalent_firewall" {
  name        = "${var.name}-firewall"
  description = "Allow traffic to Covalent server"
  vpc_id      = var.vpc_id == "" ? module.vpc.vpc_id : var.vpc_id

  ingress {
    description = "Allow SSH Access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.myip.body)}/32"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
