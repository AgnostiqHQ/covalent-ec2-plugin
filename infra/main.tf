provider "aws" {
    profile = "default"
    region = local.region
    shared_config_files = ["~/.aws/config"]
    shared_credentials_files = ["~/.aws/credentials"]
}

locals {
  name   = "test"
  region = "ca-central-1"

  user_data = <<-EOT
  #!/usr/bin/bash
  echo "Hello EC2!"
  EOT

  tags = {
    Owner       = "covalent-ec2"
    Environment = "covalent-ec2"
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

    azs              = ["${local.region}a", "${local.region}b", "${local.region}d"]
    public_subnets   = ["10.99.0.0/24", "10.99.1.0/24", "10.99.2.0/24"]
    private_subnets  = ["10.99.3.0/24", "10.99.4.0/24", "10.99.5.0/24"]
    tags = local.tags
}

data "aws_ami" "amazon_linux" {
    most_recent = true
    owners = ["amazon"]

    filter {
        name = "name"
        values = ["amzn-ami-hvm-*-x86_64-gp2"]
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
    egress_rules = ["all-all"]

    tags = local.tags
    
}



################################################################################
# EC2 Module
################################################################################

module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 3.0"

  name    = local.name
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  availability_zone      = element(module.vpc.azs, 0)
  subnet_id              = element(module.vpc.private_subnets, 0)
  vpc_security_group_ids = [module.security_group.security_group_id]
  monitoring             = true
  associate_public_ip_address = true

  user_data_base64 = base64encode(local.user_data)


  tags = local.tags
}
  