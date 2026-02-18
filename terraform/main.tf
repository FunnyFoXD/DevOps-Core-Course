terraform {
  required_version = ">= 1.9"
  
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

provider "yandex" {
  zone      = var.zone
  folder_id = var.folder_id
  service_account_key_file = var.service_account_key_file
}

# Get latest Ubuntu 22.04 LTS image
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# Use existing default network instead of creating new one
data "yandex_vpc_network" "default" {
  name = "default"
}

# Create subnet in existing default network
resource "yandex_vpc_subnet" "lab04_subnet" {
  name           = "${var.project_name}-subnet"
  zone           = var.zone
  network_id     = data.yandex_vpc_network.default.id
  v4_cidr_blocks = [var.subnet_cidr]
}

# Create security group in existing default network
resource "yandex_vpc_security_group" "lab04_sg" {
  name       = "${var.project_name}-sg"
  network_id = data.yandex_vpc_network.default.id

  ingress {
    description    = "SSH"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.ssh_allowed_cidr]
  }

  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Custom port 5000"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outbound traffic"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create compute instance
resource "yandex_compute_instance" "lab04_vm" {
  name        = "${var.project_name}-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    core_fraction = 20  # Free tier: 20% of 2 cores
    memory        = 1    # 1 GB RAM
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10  # 10 GB HDD (free tier)
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab04_subnet.id
    security_group_ids = [yandex_vpc_security_group.lab04_sg.id]
    nat                = true  # Assign public IP
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = var.project_name
    lab     = "lab04"
    managed = "terraform"
  }
}