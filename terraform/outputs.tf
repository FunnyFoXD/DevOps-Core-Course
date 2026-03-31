output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = yandex_compute_instance.lab04_vm.network_interface[0].ip_address
}

output "vm_id" {
  description = "ID of the created VM"
  value       = yandex_compute_instance.lab04_vm.id
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address}"
}

output "network_id" {
  description = "ID of the VPC network (using existing default network)"
  value       = data.yandex_vpc_network.default.id
}