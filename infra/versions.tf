terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 4.23"
        }
    }
    required_version = ">= 1.2.0"
}
