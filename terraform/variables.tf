variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "devops-lab04"
}

variable "zone" {
  description = "Yandex Cloud zone (e.g., ru-central1-a)"
  type        = string
  default     = "ru-central1-a"
}

variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
  sensitive   = true
}

variable "subnet_cidr" {
  description = "CIDR block for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_user" {
  description = "SSH username for VM access"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access (restrict to your IP for security)"
  type        = string
  default     = "0.0.0.0/0" # WARNING: Change this to your IP for production!
}

variable "service_account_key_file" {
  description = "Path to Yandex Cloud service account key JSON file"
  type        = string
  default     = "~/.yandex/authorized_key.json"
}