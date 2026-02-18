"""
Pulumi infrastructure code for Lab 4
Creates a VM in Yandex Cloud (same infrastructure as Terraform)
"""
import pulumi
import pulumi_yandex as yandex

# Configuration
config = pulumi.Config()
project_name = config.get("project_name", "devops-lab04")
zone = config.get("zone", "ru-central1-a")
folder_id = config.require("folder_id")

# Configure Yandex Cloud provider
service_account_key_file = config.get("yandex:serviceAccountKeyFile") or config.get("service_account_key_file")
if not service_account_key_file:
    raise Exception("Please set 'yandex:serviceAccountKeyFile' or 'service_account_key_file' in Pulumi config")

yandex_provider = yandex.Provider(
    "yandex-provider",
    folder_id=folder_id,
    service_account_key_file=service_account_key_file
)
subnet_cidr = config.get("subnet_cidr", "10.0.2.0/24")  # Different CIDR to avoid conflict with Terraform subnet
ssh_user = config.get("ssh_user", "ubuntu")
ssh_allowed_cidr = config.get("ssh_allowed_cidr", "0.0.0.0/0")

# Read SSH public key
try:
    ssh_key_path = config.get("ssh_public_key_path", "~/.ssh/id_rsa.pub")
    if ssh_key_path.startswith("~"):
        import os
        ssh_key_path = os.path.expanduser(ssh_key_path)
    
    with open(ssh_key_path, "r") as f:
        ssh_public_key = f.read().strip()
except FileNotFoundError:
    raise Exception(f"SSH public key not found at {ssh_key_path}. Please generate one or update the path.")

# Get latest Ubuntu 22.04 LTS image
ubuntu_image = yandex.get_compute_image(
    family="ubuntu-2204-lts",
    folder_id="standard-images"
)

# Use existing default network instead of creating new one
# (to avoid quota error: vpc.networks.count exceeded)
default_network = yandex.get_vpc_network(name="default", folder_id=folder_id)

# Create subnet in existing default network
subnet = yandex.VpcSubnet(
    f"{project_name}-subnet-pulumi",
    name=f"{project_name}-subnet-pulumi",
    zone=zone,
    network_id=default_network.id,  # Use existing default network
    v4_cidr_blocks=[subnet_cidr],
    folder_id=folder_id,
    opts=pulumi.ResourceOptions(provider=yandex_provider)
)

# Create security group
security_group = yandex.VpcSecurityGroup(
    f"{project_name}-sg-pulumi",
    name=f"{project_name}-sg-pulumi",
    network_id=default_network.id,  # Use existing default network
    folder_id=folder_id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[ssh_allowed_cidr]
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"]
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Custom port 5000",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all outbound traffic",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ],
    opts=pulumi.ResourceOptions(provider=yandex_provider)
)

# Create compute instance
vm = yandex.ComputeInstance(
    f"{project_name}-vm-pulumi",
    name=f"{project_name}-vm-pulumi",
    platform_id="standard-v2",
    zone=zone,
    folder_id=folder_id,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        core_fraction=20,  # Free tier: 20% of 2 cores
        memory=1  # 1 GB RAM
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=10,  # 10 GB HDD (free tier)
            type="network-hdd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            security_group_ids=[security_group.id],
            nat=True  # Assign public IP
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}"
    },
    labels={
        "project": project_name,
        "lab": "lab04",
        "managed": "pulumi"
    },
    opts=pulumi.ResourceOptions(provider=yandex_provider)
)

# Export outputs
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("vm_id", vm.id)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ", ssh_user, "@", vm.network_interfaces[0].nat_ip_address))
pulumi.export("network_id", default_network.id)

