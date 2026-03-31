# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

## Lab Status

**Task 1 (Terraform)**: Completed
- VM created: `fhme74phqjtvibqipa5j` (IP: `89.169.156.227`)
- SSH access verified
- VM kept for Lab 5

**Task 2 (Pulumi)**: Completed
- VM created: `fhmb1kcrg8fto11etiu5` (IP: `89.169.159.192`)
- SSH access verified
- VM can be destroyed after Lab 4 completion

---

## 1. Cloud Provider & Infrastructure

### Cloud Provider Chosen: Yandex Cloud

**Rationale:**
- Recommended for Russia with free tier available
- No credit card required initially
- Good documentation in Russian
- Free tier includes: 1 VM with 20% vCPU, 1 GB RAM, 10 GB SSD storage

### Instance Configuration

- **Instance Type**: standard-v2 platform
- **CPU**: 2 cores @ 20% (free tier)
- **Memory**: 1 GB RAM
- **Storage**: 10 GB HDD (network-hdd)
- **OS**: Ubuntu 22.04 LTS
- **Zone**: ru-central1-a

### Resources Created

1. **VPC Network** (existing)
   - Name: `default`
   - Network ID: `enp0s0pv9jb1vgcinchj`
   - Note: Terraform was updated to reuse the existing `default` network because of quota error `vpc.networks.count exceeded` when trying to create a new network.

2. **Subnet** (`yandex_vpc_subnet`)
   - Name: `devops-lab04-subnet`
   - CIDR: `10.0.1.0/24`
   - Zone: `ru-central1-a`

3. **Security Group** (`yandex_vpc_security_group`)
   - Name: `devops-lab04-sg`
   - Rules:
     - SSH (port 22) - restricted to configured CIDR
     - HTTP (port 80) - open to all
     - Custom port 5000 - open to all (for future app deployment)
     - All outbound traffic allowed

4. **Compute Instance** (`yandex_compute_instance`)
   - Name: `devops-lab04-vm` (instance id: `fhme74phqjtvibqipa5j`)
   - Public IP assigned (NAT enabled)
   - SSH key configured in metadata

### Total Cost

**$0** - All resources use Yandex Cloud free tier.

---

## 2. Terraform Implementation

### Terraform Version

```bash
$ terraform version
Terraform v1.14.5
```

### Project Structure

```
terraform/
├── .gitignore           # (should exclude state files)
├── main.tf              # Main resources and provider config
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars     # Variable values (gitignored)
└── README.md            # Setup instructions
```

### Key Configuration Decisions

1. **Provider**: Yandex Cloud (`yandex-cloud/yandex`)
2. **Data Source**: Used `yandex_compute_image` to dynamically get latest Ubuntu 22.04 LTS
3. **Variables**: All configurable values moved to variables for reusability
4. **Security**: SSH access restricted to specific CIDR (configurable via variable)
5. **Labels**: Added project and lab labels for resource identification
6. **Outputs**: Exported public IP, private IP, VM ID, and SSH command

### Challenges Encountered

1. **SSH Key Format**: Yandex Cloud requires specific format: `user:public-key-content`
2. **Zone Selection**: Need to ensure zone matches folder availability
3. **Free Tier Limits**: Must use `core_fraction = 20` for free tier eligibility
4. **VPC Quota**: Initial apply failed with `vpc.networks.count exceeded` → fixed by reusing existing `default` network.
5. **Path Expansion**: `~` was not expanded for `service_account_key_file` → fixed by using absolute path in `terraform.tfvars`.

### Terminal Output

#### terraform init

```bash
$ terraform init

Initializing the backend...

Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.100"...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0 (self-signed, key ID E40F590B50BB8E40)

Terraform has created a lock file .terraform.lock.hcl to record the provider selections it made above.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.
```

#### terraform plan

```bash
$ terraform plan

data.yandex_vpc_network.default: Reading...
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 1s [id=fd8t9g30r3pc23et5krl]
data.yandex_vpc_network.default: Read complete after 1s [id=enp0s0pv9jb1vgcinchj]

Terraform will perform the following actions:
  # yandex_vpc_subnet.lab04_subnet will be created
  # yandex_vpc_security_group.lab04_sg will be created
  # yandex_compute_instance.lab04_vm will be created

Plan: 3 to add, 0 to change, 0 to destroy.

Warning: Cannot connect to YC tool initialization service. Network connectivity to the service is required for provider version control.
```

#### terraform apply

```bash
$ terraform apply

yandex_vpc_subnet.lab04_subnet: Creating...
yandex_vpc_security_group.lab04_sg: Creating...
yandex_vpc_subnet.lab04_subnet: Creation complete after 1s [id=e9bktdresnati8lilo1k]
yandex_vpc_security_group.lab04_sg: Creation complete after 3s [id=enpcn8b34rpnihid0p7d]
yandex_compute_instance.lab04_vm: Creating...
yandex_compute_instance.lab04_vm: Still creating... [10s elapsed]
yandex_compute_instance.lab04_vm: Still creating... [40s elapsed]
yandex_compute_instance.lab04_vm: Creation complete after 46s [id=fhme74phqjtvibqipa5j]

Warning: Cannot connect to YC tool initialization service. Network connectivity to the service is required for provider version control.

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

network_id = "enp0s0pv9jb1vgcinchj"
ssh_command = "ssh ubuntu@89.169.156.227"
vm_id = "fhme74phqjtvibqipa5j"
vm_private_ip = "10.0.1.3"
vm_public_ip = "89.169.156.227"
```

#### SSH Connection

```bash
$ ssh ubuntu@89.169.156.227

ubuntu@fhme74phqjtvibqipa5j:~$ hostname
fhme74phqjtvibqipa5j

ubuntu@fhme74phqjtvibqipa5j:~$ ip addr show
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 10.0.1.3/24 metric 100 brd 10.0.1.255 scope global dynamic eth0

ubuntu@fhme74phqjtvibqipa5j:~$ uname -a
Linux fhme74phqjtvibqipa5j 5.15.0-170-generic #180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
```

---

## 3. Pulumi Implementation

### Pulumi Version and Language

- **Pulumi Version**: 3.x
- **Language**: Python 3.x
- **Provider**: `pulumi-yandex`

### How Code Differs from Terraform

**Terraform (HCL - Declarative):**
```hcl
resource "yandex_compute_instance" "lab04_vm" {
  name        = "${var.project_name}-vm"
  platform_id = "standard-v2"
  zone        = var.zone
  ...
}
```

**Pulumi (Python - Imperative):**
```python
vm = yandex.compute.Instance(
    f"{project_name}-vm",
    name=f"{project_name}-vm",
    platform_id="standard-v2",
    zone=zone,
    ...
)
```

### Key Differences

1. **Language**: Python allows full programming features (loops, functions, classes)
2. **State Management**: Pulumi uses Pulumi Cloud (or self-hosted) vs local state file
3. **Configuration**: Uses `pulumi config` commands vs `terraform.tfvars`
4. **Type Safety**: Python provides better IDE support and type checking
5. **Logic**: Can use Python libraries, conditionals, loops naturally

### Advantages Discovered

1. **IDE Support**: Better autocomplete and error detection
2. **Code Reuse**: Can create functions/classes for common patterns
3. **Testing**: Can write unit tests for infrastructure code
4. **Secrets**: Encrypted by default in Pulumi Cloud
5. **Familiar Language**: If you know Python, easier to learn

### Challenges Encountered

1. **SSH Key Reading**: Need to handle file path expansion (`~/.ssh/...`)
2. **Output Formatting**: Pulumi outputs are different from Terraform
3. **State Location**: Need to understand Pulumi Cloud vs self-hosted backend
4. **API Syntax Differences**: 
   - Use `get_compute_image()` instead of `compute.get_image()`
   - Use `VpcSecurityGroup` instead of `vpc.SecurityGroup`
   - Use `ingresses`/`egresses` (plural) instead of `ingress`/`egress`
   - Use `get_vpc_network()` instead of `vpc.get_network()`
5. **Provider Configuration**: Need to explicitly create and pass `Provider` resource with `folder_id` and `service_account_key_file` to all resources
6. **Setuptools Compatibility**: Python 3.12 requires `setuptools<70` for `pkg_resources` compatibility with `pulumi-yandex` package
7. **Resource Naming Conflicts**: Had to use unique names (`-pulumi` suffix) to avoid conflicts with Terraform-created resources in the same folder
8. **Local Backend Setup**: Used `pulumi login --local` with empty passphrase for local state management

### Terminal Output

#### pulumi preview

```bash
$ cd pulumi
$ PULUMI_CONFIG_PASSPHRASE="" pulumi preview

Previewing update (dev):

 +  pulumi:providers:yandex yandex-provider create 
 +  yandex:index:VpcSubnet devops-lab04-subnet-pulumi create 
 +  yandex:index:VpcSecurityGroup devops-lab04-sg-pulumi create 
 +  yandex:index:ComputeInstance devops-lab04-vm-pulumi create 
    pulumi:pulumi:Stack devops-lab04-dev  
Outputs:
  + network_id   : "enp0s0pv9jb1vgcinchj"
  + ssh_command  : [unknown]
  + vm_id        : [unknown]
  + vm_private_ip: [unknown]
  + vm_public_ip : [unknown]

Resources:
    + 4 to create
```

#### pulumi up

```bash
$ PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes

Updating (dev):

 +  pulumi:providers:yandex yandex-provider creating (0s) 
 +  pulumi:providers:yandex yandex-provider created (0.00s) 
 +  yandex:index:VpcSubnet devops-lab04-subnet-pulumi creating (0s) 
 +  yandex:index:VpcSecurityGroup devops-lab04-sg-pulumi creating (0s) 
 +  yandex:index:VpcSubnet devops-lab04-subnet-pulumi created (1s) 
 +  yandex:index:VpcSecurityGroup devops-lab04-sg-pulumi created (2s) 
 +  yandex:index:ComputeInstance devops-lab04-vm-pulumi creating (0s) 
 +  yandex:index:ComputeInstance devops-lab04-vm-pulumi created (58s) 
    pulumi:pulumi:Stack devops-lab04-dev  
Outputs:
  + network_id   : "enp0s0pv9jb1vgcinchj"
  + ssh_command  : "ssh ubuntu@89.169.159.192"
  + vm_id        : "fhmb1kcrg8fto11etiu5"
  + vm_private_ip: "10.0.2.6"
  + vm_public_ip : "89.169.159.192"

Resources:
    + 4 created

Duration: 1m0s
```

#### SSH Connection Proof

```bash
$ ssh ubuntu@89.169.159.192

ubuntu@fhmb1kcrg8fto11etiu5:~$ hostname
fhmb1kcrg8fto11etiu5

ubuntu@fhmb1kcrg8fto11etiu5:~$ ip addr show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether d0:0d:b0:d1:9b:82 brd ff:ff:ff:ff:ff:ff
    altname enp7s0
    inet 10.0.2.6/24 metric 100 brd 10.0.2.255 scope global dynamic eth0
       valid_lft 4294967268sec preferred_lft 4294967268sec
    inet6 fe80::d20d:b0ff:fed1:9b82/64 scope link 
       valid_lft forever preferred_lft forever

ubuntu@fhmb1kcrg8fto11etiu5:~$ uname -a
Linux fhmb1kcrg8fto11etiu5 5.15.0-170-generic #180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
```

**Resources Created:**
- VPC Subnet: `devops-lab04-subnet-pulumi` (CIDR: `10.0.2.0/24`)
- Security Group: `devops-lab04-sg-pulumi` (SSH, HTTP, port 5000)
- Compute Instance: `devops-lab04-vm-pulumi` (VM ID: `fhmb1kcrg8fto11etiu5`)
- Network: Using existing `default` network (ID: `enp0s0pv9jb1vgcinchj`)

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

**Terraform** was easier to learn initially because:
- HCL syntax is simple and declarative
- Large community and extensive documentation
- Many examples available for common use cases
- Clear separation between configuration and logic

**Pulumi** required more setup:
- Need to understand Python (or chosen language)
- Pulumi Cloud account setup (or self-hosted backend)
- Less examples compared to Terraform
- But if you know Python, the learning curve is actually easier

### Code Readability

**Terraform (HCL)** is more readable for simple infrastructure:
- Clear resource blocks
- Easy to see what resources are being created
- Less "noise" from programming language syntax

**Pulumi (Python)** is more readable for complex logic:
- Can use functions and classes to organize code
- Better for reusable patterns
- More expressive for conditional logic

### Debugging

**Terraform** debugging:
- Clear error messages pointing to specific resources
- `terraform plan` shows exactly what will change
- State file can be inspected directly
- But limited debugging tools for logic errors

**Pulumi** debugging:
- Can use Python debugger (pdb)
- Better IDE integration for debugging
- More detailed error messages with stack traces
- Can add print statements for debugging

### Documentation

**Terraform** has better documentation:
- Official docs are comprehensive
- Terraform Registry has excellent provider docs
- Many tutorials and guides available
- Community support is extensive

**Pulumi** documentation is good but smaller:
- Official docs are well-structured
- Pulumi Registry exists but smaller
- Fewer community examples
- But examples are often more complete

### Use Case

**Use Terraform when:**
- Team prefers declarative approach
- Need maximum community support
- Working with simple to moderate complexity
- Want to avoid programming language dependencies
- Need to manage state locally

**Use Pulumi when:**
- Team is comfortable with programming languages
- Need complex logic and code reuse
- Want better IDE support and type checking
- Need to write tests for infrastructure
- Prefer imperative approach with full language features

---

## 5. Lab 5 Preparation & Cleanup

### VM for Lab 5

**Decision**: **Keeping Terraform VM for Lab 5**
- **Current Terraform VM (running)**: `89.169.156.227` (`ssh ubuntu@89.169.156.227`)
- **Keeping VM**: **Yes**
- **Which VM**: **Terraform created** (VM ID: `fhme74phqjtvibqipa5j`)
- **Alternative**: N/A - using Terraform VM

### Cleanup Status

**Terraform Resources:**
- [ ] Destroyed (if not keeping for Lab 5)
- [x] **Still running** (keeping for Lab 5)
  - VM ID: `fhme74phqjtvibqipa5j`
  - Public IP: `89.169.156.227`
  - Subnet: `devops-lab04-subnet` (CIDR: `10.0.1.0/24`)
  - Security Group: `devops-lab04-sg`

**Pulumi Resources:**
- [x] **Created and tested** (can be destroyed after verification)
  - VM ID: `fhmb1kcrg8fto11etiu5`
  - Public IP: `89.169.159.192`
  - Subnet: `devops-lab04-subnet-pulumi` (CIDR: `10.0.2.0/24`)
  - Security Group: `devops-lab04-sg-pulumi`
- [ ] Destroyed (after Lab 4 completion)

**Verification:**
- [x] **SSH access proof** (see SSH Connection section above)
- [ ] Cloud console screenshot showing resource status (optional)

---

## Bonus Tasks

### Part 1: GitHub Actions for IaC Validation

See `.github/workflows/terraform-ci.yml` for automated validation workflow.

### Part 2: GitHub Repository Import

See `terraform/github/` directory for GitHub repository import configuration.

---

## Notes

- All secrets and credentials are excluded from Git via `.gitignore`
- State files are never committed
- SSH keys are kept secure locally
- Free tier resources used to minimize costs

