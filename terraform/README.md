# Terraform Infrastructure for Lab 4

This directory contains Terraform configuration to provision a virtual machine in Yandex Cloud.

## Prerequisites

1. **Install Terraform**
   ```bash
   # Check if installed
   terraform version
   
   # Install if needed (Linux)
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install terraform
   ```

2. **Yandex Cloud Setup**
   - Create account at [Yandex Cloud](https://cloud.yandex.com/)
   - Create a folder in Yandex Cloud Console
   - Get your folder ID from the console
   - Create a service account or use OAuth token
   - Generate SSH key pair if you don't have one:
     ```bash
     ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
     ```

3. **Configure Variables**
   
   Create `terraform.tfvars` file (this file is gitignored):
   ```hcl
   project_name = "devops-lab04"
   zone         = "ru-central1-a"
   folder_id    = "your-folder-id-here"
   yandex_token = "your-token-here"
   ssh_user     = "ubuntu"
   ssh_public_key_path = "~/.ssh/id_rsa.pub"
   ssh_allowed_cidr = "YOUR.IP.ADDRESS/32"  # Restrict SSH to your IP
   ```

   **OR** use environment variables:
   ```bash
   export YC_TOKEN="your-token"
   export YC_FOLDER_ID="your-folder-id"
   ```

## Usage

1. **Initialize Terraform**
   ```bash
   cd terraform
   terraform init
   ```

2. **Format and Validate**
   ```bash
   terraform fmt
   terraform validate
   ```

3. **Plan Changes**
   ```bash
   terraform plan
   ```

4. **Apply Infrastructure**
   ```bash
   terraform apply
   ```

5. **Connect to VM**
   ```bash
   # Get SSH command from output
   terraform output ssh_command
   
   # Or connect directly
   ssh ubuntu@$(terraform output -raw vm_public_ip)
   ```

6. **Destroy Infrastructure**
   ```bash
   terraform destroy
   ```

## Resources Created

- VPC Network
- Subnet
- Security Group (SSH, HTTP, port 5000)
- Compute Instance (free tier: 2 cores @ 20%, 1 GB RAM, 10 GB disk)

## Cost

This configuration uses Yandex Cloud free tier:
- 1 VM with 20% vCPU, 1 GB RAM
- 10 GB SSD storage
- Should be $0 cost

## Security Notes

- **IMPORTANT**: Change `ssh_allowed_cidr` in `terraform.tfvars` to your IP address for better security
- Never commit `terraform.tfvars` or state files to Git
- Keep your Yandex Cloud token secure

## Alternative Cloud Providers

To use AWS instead of Yandex Cloud, see `main.tf.aws.example` (if created).

