output "hostname" {
  value       = aws_instance.covalent_svc_instance.public_dns
  description = "Hostname assigned to the EC2 instance"
}

output "username" {
  value       = local.username
  description = "Username used to connect to the EC2 instance"
}
