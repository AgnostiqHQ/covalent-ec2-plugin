terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 4.16"
        }
    }
    required_version = ">= 1.2.0"
}

provider "aws" {
    profile = "default"
    region = "ca-central-1"
}

# ID of EC2 instance would be aws_instance.covalent_server
resource "aws_instance" "covalent_server" {
    ami = "ami-00f881f027a6d74a0"
    instance_type = "t2.micro"

    tags = { 
        Name = "CovalentEC2Instance"
    }
}