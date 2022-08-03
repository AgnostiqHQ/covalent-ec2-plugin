provider "aws" {
    profile = "default"
    region = local.region
    shared_config_files = ["~/.aws/config"]
    shared_credentials_files = ["~/.aws/credentials"]
}

locals {
  name   = "covalent-ec2"
  region = "ca-central-1"
  bucket = "covalent-ec2-bucket"
  environment = "covalent-ec2"

  user_data = <<-EOT
  #!/usr/bin/bash
  cd ~
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
  bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda
  rm Miniconda3-latest-Linux-x86_64.sh
  echo 'export PATH="~/miniconda/bin:$PATH"' >> ~/.bashrc 
  # Refresh basically
  source .bashrc
  conda update conda -y
  conda init bash
  source .bashrc
  conda create -n covalent-ec2-setup python=3.8.10 -y
  conda activate covalent-ec2-setup 
  echo 'Installing Covalent pre-release and dependencies'
  pip install covalent --pre
  covalent --version
  pip install cloudpickle
  pip install botocore
  pip install boto3

  EOT

  tags = {
    Owner       = local.environment
    Environment = local.environment
  }
}

################################################################################
# Supporting Resources
################################################################################

module "vpc" {
    source = "terraform-aws-modules/vpc/aws"
    version = "~> 3.0"

    name = local.name
    cidr = "10.99.0.0/18"
    enable_dns_hostnames = true
    enable_dns_support = true
    azs              = ["${local.region}a"]
    public_subnets   = ["10.99.0.0/24"]
    private_subnets  = ["10.99.3.0/24"]
    tags = local.tags
}

data "aws_ami" "ubuntu" {
    most_recent = true
    owners = ["099720109477"]

    filter {
        name = "name"
        values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
    }

    filter {
        name = "virtualization-type"
        values = ["hvm"]
    }
}

module "security_group" {
    source = "terraform-aws-modules/security-group/aws"
    version = "~> 4.0"

    name = "${local.name}-security-gp"
    description = "Test security group for usage with EC2 instance"
    vpc_id = module.vpc.vpc_id

    ingress_cidr_blocks = ["0.0.0.0/0"]
    ingress_rules = ["http-80-tcp", "all-icmp"]
    ingress_with_cidr_blocks = [
      {
        from_port = 22
        to_port   = 22
        protocol  = "tcp"
        cidr_blocks = "0.0.0.0/0"
      }
    ]
    egress_rules = ["all-all"]

    tags = local.tags
    
}

resource "aws_s3_bucket" "covalent_ec2_bucket" {
  bucket = local.bucket

  tags = {
    Name = local.bucket
  }
}

resource "aws_s3_bucket_acl" "covalent_ec2_bucket_acl" {

  bucket = aws_s3_bucket.covalent_ec2_bucket.id
  acl = "public-read-write"
  depends_on = [module.ec2_instance.id, module.vpc.id]
  
}

resource "aws_eip" "lb" {
  instance = module.ec2_instance.id
  vpc      = true
}
resource "aws_internet_gateway" "covalent_ec2_gw" {
  # vpc_id = module.vpc.vpc_id
}

################################################################################
# EC2 Module
################################################################################

module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 3.0"

  name    = local.name
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t2.micro"
  availability_zone      = element(module.vpc.azs, 0)
  subnet_id              = element(module.vpc.private_subnets, 0)
  vpc_security_group_ids = [module.security_group.security_group_id]
  monitoring             = true
  associate_public_ip_address = true
  depends_on = [aws_internet_gateway.covalent_ec2_gw]

  user_data_base64 = base64encode(local.user_data)

  tags = local.tags
}

