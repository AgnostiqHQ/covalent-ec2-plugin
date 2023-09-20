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

variable "name" {
  default     = "covalent-svc"
  description = "Name used to prefix AWS resources"
}

variable "aws_region" {
  default     = "us-east-1"
  description = "Region where resources for the EC2 plugin are deployed"
}

variable "aws_profile" {
  default     = "default"
  description = "AWS profile used when authenticating"
}

variable "aws_credentials" {
  default     = "~/.aws/credentials"
  description = "AWS credentials file to use when authenticating"
}

variable "python3_path" {
  default = "/home/ubuntu/miniconda3/envs/covalent-dev/bin/python3"
  description = "Python3 path in the active conda environment of the EC2 instance"
}

variable "remote_cache" {
  default = "/home/ubuntu/.cache/covalent"
  description = "Remote cache directory"

}
variable "key_name" {
  default     = ""
  description = "Key pair name"
}

variable "vpc_id" {
  default     = ""
  description = "Existing VPC ID"
}

variable "subnet_id" {
  default     = ""
  description = "Existing subnet ID"
}

variable "vpc_cidr" {
  default     = "10.0.0.0/24"
  description = "VPC CIDR range"
}

variable "instance_type" {
  default     = "t2.micro"
  description = "Server instance type"
}

variable "disk_size" {
  default     = 8
  description = "Server disk size"
}

variable "key_file" {
  default     = ""
  description = "Private key used for SSH provisioner"
}
