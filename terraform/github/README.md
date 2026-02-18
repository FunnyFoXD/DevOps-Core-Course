# GitHub Repository Management with Terraform

This directory contains Terraform configuration to manage the DevOps-Core-Course GitHub repository.

## Purpose

This demonstrates importing existing infrastructure (GitHub repository) into Terraform management. This is useful for:

1. **Version Control**: Track repository configuration changes over time
2. **Consistency**: Standardize settings across repositories
3. **Automation**: Changes require code review via PRs
4. **Documentation**: Code is living documentation of repository settings
5. **Disaster Recovery**: Quickly recreate repository settings from code

## Prerequisites

1. **GitHub Personal Access Token**
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope (all repository permissions)
   - Copy token (shown only once!)

2. **Configure Token**
   
   Create `terraform.tfvars` in this directory:
   ```hcl
   github_token = "your-token-here"
   ```
   
   **OR** use environment variable:
   ```bash
   export GITHUB_TOKEN="your-token-here"
   ```

## Usage

### 1. Import Existing Repository

The repository already exists, so we need to import it:

```bash
cd terraform/github

# Initialize Terraform
terraform init

# Import existing repository
terraform import github_repository.course_repo DevOps-Core-Course
```

### 2. Verify Import

After import, check if state matches reality:

```bash
# This will show differences between code and actual repository
terraform plan
```

### 3. Update Configuration

If `terraform plan` shows differences, update `main.tf` to match actual repository settings, then run `terraform plan` again until it shows "No changes".

### 4. Apply Changes

Once configuration matches reality:

```bash
terraform apply
```

Now Terraform manages the repository! Future changes to repository settings should go through Terraform.

## What Can Be Managed

- Repository name, description, visibility
- Features (issues, wiki, projects, downloads)
- Merge options (merge commit, squash, rebase)
- Branch protection rules
- Topics/tags
- Collaborators and teams
- Webhooks
- Repository secrets

## Security Notes

- **NEVER** commit `terraform.tfvars` with token to Git
- Token is marked as `sensitive` in variables
- Use environment variables or GitHub Secrets in CI/CD

## Why Import Existing Resources?

In real-world scenarios, you often have:
- Infrastructure created manually (before IaC adoption)
- Resources created by other tools or people
- Legacy systems that need to be managed with code

You can't just run `terraform apply` - resources already exist!

**The Solution**: `terraform import` brings existing resources into Terraform management:
1. Write Terraform config describing the resource
2. Run `terraform import` to link config to real resource
3. Terraform now manages that resource
4. Future changes go through Terraform

## Benefits

1. **Version Control**: Track configuration changes over time
2. **Consistency**: Standardize configuration across resources
3. **Automation**: Changes require code review
4. **Documentation**: Code is living documentation
5. **Disaster Recovery**: Quickly recreate from code
6. **Team Collaboration**: Multiple people can work on infrastructure

## Resources

- [GitHub Provider Documentation](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [Repository Resource](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository)
- [Import Guide](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository#import)

