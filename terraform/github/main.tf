# GitHub Provider Configuration
# This manages the DevOps-Core-Course repository using Terraform

terraform {
  required_version = ">= 1.9"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  token = var.github_token
}

# Import existing repository
resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps course lab assignments and projects"
  visibility  = "public"

  has_issues    = true
  has_wiki      = false
  has_projects  = false
  has_downloads = true

  allow_merge_commit = true
  allow_squash_merge = true
  allow_rebase_merge = true

  delete_branch_on_merge = true

  topics = [
    "devops",
    "terraform",
    "pulumi",
    "docker",
    "kubernetes",
    "ci-cd"
  ]

  # Default branch protection (optional - uncomment if needed)
  # default_branch = "master"
}

