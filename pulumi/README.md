# Pulumi Infrastructure for Lab 4

This directory contains Pulumi code to provision a virtual machine in Yandex Cloud (same infrastructure as Terraform).

## Prerequisites

1. **Install Pulumi**
   ```bash
   # Check if installed
   pulumi version
   
   # Install if needed (Linux)
   curl -fsSL https://get.pulumi.com | sh
   ```

2. **Python Setup**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Yandex Cloud Setup**
   - Same as Terraform setup
   - Create account, folder, get folder ID
   - Create service account or use OAuth token
   - Generate SSH key pair if needed

4. **Configure Pulumi**
   
   Create a stack (e.g., "dev"):
   ```bash
   pulumi stack init dev
   ```
   
   Set configuration:
   ```bash
   pulumi config set project_name devops-lab04
   pulumi config set zone ru-central1-a
   pulumi config set folder_id your-folder-id-here
   pulumi config set --secret yandex:token your-token-here
   pulumi config set ssh_user ubuntu
   pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub
   pulumi config set ssh_allowed_cidr YOUR.IP.ADDRESS/32
   ```
   
   **OR** use environment variables:
   ```bash
   export YC_TOKEN="your-token"
   export YC_FOLDER_ID="your-folder-id"
   ```

## Usage

1. **Preview Changes**
   ```bash
   cd pulumi
   source venv/bin/activate
   pulumi preview
   ```

2. **Apply Infrastructure**
   ```bash
   pulumi up
   ```

3. **View Outputs**
   ```bash
   pulumi stack output
   pulumi stack output ssh_command
   ```

4. **Connect to VM**
   ```bash
   # Get SSH command from output
   pulumi stack output ssh_command
   
   # Or connect directly
   ssh ubuntu@$(pulumi stack output --show-secrets vm_public_ip)
   ```

5. **Destroy Infrastructure**
   ```bash
   pulumi destroy
   ```

## Resources Created

Same as Terraform:
- VPC Network
- Subnet
- Security Group (SSH, HTTP, port 5000)
- Compute Instance (free tier: 2 cores @ 20%, 1 GB RAM, 10 GB disk)

## Comparison with Terraform

**Similarities:**
- Same infrastructure resources
- Same free tier configuration
- Same security group rules

**Differences:**
- **Language**: Python (imperative) vs HCL (declarative)
- **State**: Pulumi Cloud (or self-hosted) vs local state file
- **Logic**: Full Python features (loops, functions, classes) vs limited HCL
- **IDE Support**: Better autocomplete and type checking in Python

## Cost

Same as Terraform - uses Yandex Cloud free tier ($0 cost).

## Security Notes

- **IMPORTANT**: Change `ssh_allowed_cidr` to your IP address
- Never commit `Pulumi.*.yaml` files with secrets to Git
- Keep your Yandex Cloud token secure

