output "hostname" {
  value       = aws_instance.covalent_ec2_instance.public_dns
  description = "Hostname assigned to the EC2 instance"
}

output "username" {
  value       = local.username
  description = "Username used to connect to the EC2 instance"
}

output "python3_path" {
  value = var.python3_path
  description = "Python 3 path in the EC2 instance"
}

output "remote_cache" {
  value = var.remote_cache
  description = "Location of Covalent cache data and state files in the EC2 instance"
}
