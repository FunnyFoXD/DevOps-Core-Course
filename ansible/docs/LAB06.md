# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Your Name  
**Date:** 2026-03-04  
**Lab Points:** 10 + 0 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Implementation details

**Roles updated:** `common`, `docker`  
**Playbook using tags:** `ansible/playbooks/provision.yml`

- **common role (`roles/common/tasks/main.yml`)**
  - Grouped package-related tasks into a `block` called "Manage common packages":
    - Updates apt cache with `ansible.builtin.apt` and `cache_valid_time`.
    - Installs `common_packages` with `state: present`.
    - `rescue` block runs `apt-get update --fix-missing` via `shell` if the block fails.
    - `always` block touches `/tmp/common_packages_completed` (log marker that the block finished).
    - `become: true` is applied once at block level instead of on each task.
    - Tags on block: `common`, `packages`.
  - Added a "Manage common users" block:
    - Ensures a user (`common_user_name`, default `devops`) exists and belongs to `common_user_groups` (default includes `sudo`).
    - Tags: `common`, `users`.
  - Timezone configuration remains as a dedicated task:
    - Uses `community.general.timezone` with `common_timezone`.
    - Tag: `common`.

- **docker role (`roles/docker/tasks/main.yml`)**
  - `Install Docker packages and repository` block:
    - Creates `/etc/apt/keyrings` directory.
    - Downloads Docker GPG key and stores it in `/etc/apt/keyrings/docker.asc`.
    - Converts the key to keyring format in `/etc/apt/keyrings/docker.gpg` with a `creates` guard.
    - Adds the Docker apt repository with `ansible.builtin.apt_repository`.
    - Installs `docker_packages` with apt; notifies handler `restart docker`.
    - `rescue` block retries apt metadata update (`apt-get update` with `sleep 10`) if the block fails (e.g., network or key issues).
    - `always` block ensures the `docker` service is enabled and running.
    - `become: true` at block level.
    - Tags: `docker`, `docker_install`.
  - `Configure Docker users and SDK` block:
    - Adds `docker_group_user` to the `docker` group.
    - Installs Python package `docker>=7.0.0` with `pip` to support Ansible Docker modules.
    - Tags: `docker`, `docker_config`.

- **Tag strategy**
  - Role-level tags (from `provision.yml`):
    - `common` — all base OS configuration.
    - `docker` — all Docker-related tasks.
  - Block-level tags:
    - `packages` — all tasks that manage common system packages.
    - `users` — all tasks that manage users in `common`.
    - `docker_install` — repository and package installation for Docker.
    - `docker_config` — user and SDK configuration for Docker.

- **Selective execution examples**
  - List tags:
    - `ansible-playbook playbooks/provision.yml --list-tags`
  - Run only Docker-related tasks:
    - `ansible-playbook playbooks/provision.yml --tags "docker"`
  - Skip `common` role:
    - `ansible-playbook playbooks/provision.yml --skip-tags "common"`
  - Run only package installation across roles:
    - `ansible-playbook playbooks/provision.yml --tags "packages"`

These runs show that tags applied at block level are visible from the playbook and allow fine-grained control together with high-level role tags.

### Research answers

- **Q: What happens if rescue block also fails?**  
  If a task inside the `rescue` section fails, the entire block is still considered failed. The play then behaves as for any normal failure: it stops (unless `ignore_errors` or `max_fail_percentage` is used) and moves to error handling at play level. `rescue` is an extra chance to recover, not a guarantee that the play will always succeed.

- **Q: Can you have nested blocks?**  
  Yes, Ansible allows nested `block` sections (a block inside another block). This can be used to group related tasks and apply different `when`, `tags`, or error handling at multiple levels. However, deeply nested blocks can reduce readability, so they should be used sparingly and only when they make error-handling or scoping significantly clearer.

- **Q: How do tags inherit to tasks within blocks?**  
  Tags defined on a block (or role) are inherited by all tasks inside that block. That means:
  - Running with `--tags docker_install` will execute only the tasks inside the Docker installation block.
  - Running with `--skip-tags packages` will skip all tasks in the `packages` block of `common`.
  Inheritance is additive: a task can receive tags from its block, role, and any tags defined directly on the task itself.

---

## Task 2: Docker Compose (3 pts)

### 2.1 Implementation

**Goal:** Replace raw `docker run` commands with a declarative Docker Compose–based deployment for the web application role.

- **Role rename / structure**
  - The old `app_deploy` role has been replaced by a `web_app` role.
  - Playbook `ansible/playbooks/deploy.yml` now uses:
    - `roles: [ web_app ]`

- **Docker Compose template**
  - File: `ansible/roles/web_app/templates/docker-compose.yml.j2`
  - Template structure:
    ```yaml
    version: "{{ docker_compose_version | default('3.8') }}"

    services:
      {{ app_name }}:
        image: "{{ docker_image }}:{{ docker_tag }}"
        container_name: "{{ app_name }}"
        ports:
          - "{{ app_port }}:{{ app_internal_port }}"
    {% if app_env %}
        environment:
    {% for k, v in app_env.items() %}
          {{ k }}: "{{ v }}"
    {% endfor %}
    {% endif %}
        restart: "{{ restart_policy }}"
    ```
  - The `environment` section is conditionally rendered only when `app_env` is non-empty, so Docker Compose does not see a `null` environment (which would be invalid).

- **Role defaults**
  - File: `ansible/roles/web_app/defaults/main.yml`
  - Configuration:
    ```yaml
    # Application Configuration
    app_name: devops-info-service
    docker_image: funnyfoxd/devops-info-service
    docker_tag: 2026.02
    app_port: 5000
    app_internal_port: 5000

    # Docker Compose Config
    compose_project_dir: "/opt/{{ app_name }}"
    docker_compose_version: "3.8"

    # Container restart policy
    restart_policy: unless-stopped

    # Environment variables for the app
    app_env: {}

    # Wipe Logic Control
    web_app_wipe: false
    ```
  - These defaults can be overridden via Vault-encrypted `group_vars/all.yml` if needed.

- **Role dependencies**
  - File: `ansible/roles/web_app/meta/main.yml`
  - Content:
    ```yaml
    ---
    dependencies:
      - role: docker
    ```
  - This guarantees that Docker is installed and the service is running before the `web_app` role tries to use Docker Compose.

- **Deployment tasks**
  - File: `ansible/roles/web_app/tasks/main.yml`
  - Key block:
    - Includes `wipe.yml` first (see Task 3).
    - Creates the application directory `compose_project_dir`.
    - Templates `docker-compose.yml` into that directory.
    - Calls `community.docker.docker_compose_v2` with:
      - `project_src: "{{ compose_project_dir }}"`
      - `state: present`
      - `pull: always`
    - Uses a `rescue` block to log deployment failure via `debug`.
    - Tags: `app_deploy`, `compose`.

### 2.2 Before / after comparison

- **Before (Lab 5)**
  - Raw `docker` CLI calls inside the `app_deploy` role:
    - `docker login` using credentials from Vault.
    - `docker pull` by image name and tag.
    - `docker stop` / `docker rm` for old container.
    - `docker run` with port mappings and env variables.
  - Pros: simple, minimal dependencies.
  - Cons: less declarative, harder to manage multiple containers or shared networks/volumes.

- **After (Lab 6)**
  - Declarative Docker Compose file:
    - Explicit service name and image.
    - Port mappings and environment in a YAML file.
    - Restart policy controlled via Compose.
  - `community.docker.docker_compose_v2` module:
    - Handles container creation/update.
    - Pulls images automatically with `pull: always`.
    - Uses `project_src` to keep all app state under `/opt/{{ app_name }}`.
  - Pros: easier to extend to multi-service setups, easier to reason about configuration drift, “infrastructure as code” in a single compose file.

### 2.3 Testing & idempotency

- **First run of `deploy.yml`** (after migrating to Compose):
  - Key tasks:
    - Docker role tasks: all `ok` (Docker already installed from previous labs).
    - `web_app : Create app directory` — `changed` on first run.
    - `web_app : Template docker-compose file` — `changed`.
    - `web_app : Deploy application with Docker Compose v2` — `changed`.
  - Result:
    - Docker container `devops-info-service` running.
    - `docker ps` output shows:
      - Image: `funnyfoxd/devops-info-service:2026.02`
      - Ports: `0.0.0.0:5000->5000/tcp`.
    - Health check:
      - On VM: `curl http://127.0.0.1:5000/health` returns JSON with `"status": "healthy"`.
      - From local machine: `curl http://89.169.156.227:5000/health` also returns `"status":"healthy"`.

- **Second run of `deploy.yml`**:
  - Docker role tasks reported `ok` (no changes).
  - `web_app : Template docker-compose file` and `web_app : Deploy application with Docker Compose v2` may still show `changed` because Compose updates internal state, but the resulting container configuration stays the same.
  - This behaviour is acceptable: the desired state of the service (image, ports, restart policy) remains consistent across runs.

---

## Task 3: Wipe Logic (1 pt)

### 3.1 Implementation

**Goal:** Implement safe wipe logic for the web application that requires both an explicit variable and a tag.

- **Control variable**
  - File: `ansible/roles/web_app/defaults/main.yml`
  - Variable:
    ```yaml
    web_app_wipe: false  # Default: do not wipe
    ```
  - Documentation:
    - Wipe only:
      - `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe`
    - Clean install (wipe + deploy):
      - `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"`

- **Wipe tasks**
  - File: `ansible/roles/web_app/tasks/wipe.yml`
  - Structure:
    ```yaml
    ---
    - name: Wipe web application
      block:
        - name: Stop and remove containers with Docker Compose
          community.docker.docker_compose_v2:
            project_src: "{{ compose_project_dir }}"
            state: absent
          ignore_errors: true

        - name: Remove docker-compose file
          ansible.builtin.file:
            path: "{{ compose_project_dir }}/docker-compose.yml"
            state: absent

        - name: Remove application directory
          ansible.builtin.file:
            path: "{{ compose_project_dir }}"
            state: absent

        - name: Log wipe completion
          ansible.builtin.debug:
            msg: "Application {{ app_name }} wiped successfully"

      when: web_app_wipe | bool
      tags:
        - web_app_wipe
    ```
  - Notes:
    - `ignore_errors: true` on the Docker Compose stop/remove task prevents failures when the directory or project does not exist.
    - The `when: web_app_wipe | bool` gate ensures the wipe block only runs when the variable is explicitly set to true.

- **Including wipe in main tasks**
  - File: `ansible/roles/web_app/tasks/main.yml`
  - At the top:
    ```yaml
    - name: Include wipe tasks
      ansible.builtin.include_tasks: wipe.yml
      when: web_app_wipe | bool
      tags:
        - web_app_wipe
    ```
  - Rationale:
    - Wipe tasks are executed before deployment when `web_app_wipe` is true.
    - This supports the “clean reinstall” scenario: wipe → deploy in a single playbook run.

### 3.2 Test results for wipe scenarios

**Scenario 1: Normal deployment (wipe should NOT run)**  
Command:
- `ansible-playbook playbooks/deploy.yml --ask-vault-pass`

Observations:
- `TASK [web_app : Include wipe tasks]` → `skipping` (variable `web_app_wipe` defaults to `false`).
- Container `devops-info-service` is running and healthy on port 5000.

**Scenario 2: Wipe only (remove existing deployment)**  
Command:
- `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass`

Observations:
- `Include wipe tasks` includes `wipe.yml`.
- `Stop and remove containers with Docker Compose` runs successfully (with a warning about obsolete `version` field in compose, which is harmless).
- `Remove docker-compose file` and `Remove application directory` both report `changed`.
- `Log wipe completion` message: `Application devops-info-service wiped successfully`.
- After the play:
  - `ansible webservers -a "docker ps"` shows **no containers**.
  - `ansible webservers -a "ls /opt"` no longer shows `devops-info-service` directory.

**Scenario 3: Clean reinstallation (wipe → deploy)**  
Command:
- `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass`

Observations:
- Wipe tasks run first:
  - On a clean system, `docker_compose_v2` may report `"is not a directory"`, but due to `ignore_errors: true` the play continues.
  - Directory and file removal tasks complete successfully.
  - Wipe completion message is printed.
- Deployment tasks then run:
  - `Create app directory`, `Template docker-compose file`, `Deploy application with Docker Compose v2` report `changed`.
  - `docker ps` shows the `devops-info-service` container running again.
  - `curl` from the VM and externally returns a healthy JSON response.

**Scenario 4a: Safety check (tag set, variable false)**  
Command:
- `ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass`

Observations:
- `TASK [web_app : Include wipe tasks]` → `skipping` because `web_app_wipe | bool` is false.
- `PLAY RECAP` shows `changed=0`, `failed=0`.
- `docker ps` shows the existing application container still running, confirming that wipe did not execute.

### 3.3 Research answers (Wipe Logic)

1. **Why use both variable AND tag?**  
   This forms a double safety mechanism:
   - The tag `web_app_wipe` ensures that wipe tasks are never run accidentally when deploying with generic tags.
   - The variable `web_app_wipe` must be explicitly set to `true` to allow the block to run.
   Together, they require an explicit and conscious decision to perform a destructive wipe.

2. **What's the difference between `never` tag and this approach?**  
   The `never` tag turns a task into something that will **never** run unless explicitly targeted by `--tags never`. In this lab, wipe is controlled by a meaningful tag (`web_app_wipe`) and a boolean variable. This keeps the intent clear and allows more granular conditions (e.g., run wipe only for a specific app, or only when a certain flag is set).

3. **Why must wipe logic come BEFORE deployment in `main.yml`?**  
   Wipe-before-deploy enables clean reinstalls: the old application is fully removed (containers, compose file, directory) and then a fresh deployment is applied. If the order were reversed, a “wipe then deploy” scenario would require two separate runs and could leave windows where the app is partially deployed or inconsistent.

4. **When would you want clean reinstallation vs. rolling update?**  
   - **Clean reinstall** is useful when:
     - The deployment state is corrupted or inconsistent.
     - Data is ephemeral and there is no need to preserve volumes.
     - You want to guarantee that nothing from the previous deployment remains.
   - **Rolling update** is useful when:
     - You need zero/minimal downtime.
     - Stateful data or sessions must be preserved.
     - You use blue/green or canary deployments instead of wiping everything.

5. **How would you extend this to wipe Docker images and volumes too?**  
   - Add steps to:
     - Remove images with `community.docker.docker_image` or `docker image rm`.
     - Remove volumes with `community.docker.docker_volume` or `docker volume rm`.
   - These should be separate tasks (or even a separate tag like `web_app_wipe_deep`) to avoid accidental deletion of shared images/volumes.

---

## Task 4: CI/CD (3 pts)

> Note: CI/CD workflow will be implemented in `.github/workflows/ansible-deploy.yml`. This section describes the planned architecture and configuration based on the lab requirements; the actual YAML file and screenshots will be added once the workflow is configured on GitHub.

### 4.1 Workflow architecture

- **Triggers**
  - `push` and `pull_request` to the main branch.
  - Path filters to run the workflow only when Ansible code or the workflow itself changes:
    - `ansible/**`
    - `.github/workflows/ansible-deploy.yml`

- **Jobs**
  - `lint` job:
    - Runs on `ubuntu-latest`.
    - Steps:
      - Checkout repository with `actions/checkout@v4`.
      - Set up Python with `actions/setup-python@v5`.
      - Install `ansible` and `ansible-lint` via `pip`.
      - Run `ansible-lint` against `ansible/playbooks/*.yml`.
  - `deploy` job:
    - Depends on `lint`.
    - Runs on `ubuntu-latest` (GitHub-hosted runner) or on a self-hosted runner if configured.
    - Steps:
      - Checkout code.
      - Install Ansible.
      - Configure SSH to the target VM using secrets (`SSH_PRIVATE_KEY`, `VM_HOST`, `VM_USER`).
      - Provide Vault password from `ANSIBLE_VAULT_PASSWORD` secret.
      - Run `ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file /tmp/vault_pass`.
      - Verify deployment with `curl` against `/` and `/health` endpoints.

### 4.2 Secrets configuration

- **GitHub Secrets (Repository → Settings → Secrets and variables → Actions)**
  - `ANSIBLE_VAULT_PASSWORD` — used to decrypt `group_vars/all.yml`.
  - `SSH_PRIVATE_KEY` — private key allowing SSH access from the runner to the VM.
  - `VM_HOST` — public IP or hostname of the VM.
  - `VM_USER` — SSH username on the VM.

- **Usage pattern in workflow**
  - Vault password:
    ```bash
    echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
    ansible-playbook playbooks/deploy.yml \
      -i inventory/hosts.ini \
      --vault-password-file /tmp/vault_pass
    rm /tmp/vault_pass
    ```
  - SSH:
    ```bash
    mkdir -p ~/.ssh
    echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts
    ```

### 4.3 Verification step

After running `ansible-playbook`, the workflow will:

- Wait for the app to start:
  - `sleep 10`
- Verify endpoints:
  - `curl -f http://${{ secrets.VM_HOST }}:5000 || exit 1`
  - `curl -f http://${{ secrets.VM_HOST }}:5000/health || exit 1`

If either request fails, the job fails, clearly indicating deployment issues.

### 4.4 Path filters and badge

- **Path filters motivation**
  - Avoid running the Ansible workflow when only documentation or unrelated code changes.
  - Focus CI/CD execution on infrastructure-related changes.

- **Example filter**
  ```yaml
  on:
    push:
      branches: [ main, master ]
      paths:
        - 'ansible/**'
        - '!ansible/docs/**'
        - '.github/workflows/ansible-deploy.yml'
  ```

- **Status badge**
  - To be added to `README.md`:
    ```markdown
    [![Ansible Deployment](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml)
    ```

### 4.5 Research answers (CI/CD)

1. **What are the security implications of storing SSH keys in GitHub Secrets?**  
   GitHub Secrets are encrypted at rest and scoped to the repository or organization, but anyone with write access to workflows can potentially use the secret value in a job. This means SSH keys stored as secrets should be limited to the minimal required privileges (e.g., a dedicated deployment user) and rotated regularly. Secrets should never be printed to logs or echoed directly; they should only be used in commands and temporary files with restricted permissions.

2. **How would you implement a staging → production deployment pipeline?**  
   A common approach is:
   - Two environments (VMs or clusters): staging and production.
   - Two inventories or inventory groups in Ansible.
   - GitHub Actions workflow with two deployment jobs:
     - `deploy_staging` triggered on every push or PR merge.
     - `deploy_production` triggered only on tagged releases or manual approvals (`workflow_dispatch` with environment protection rules).
   - Each job uses different secrets for `VM_HOST`, `VM_USER`, and Vault files.

3. **What would you add to make rollbacks possible?**  
   - Store previous deploy artifacts (image tags, compose files) or rely on versioned Docker images (e.g., `2026.02`, `2026.03`, not just `latest`).
   - Add a rollback playbook or additional Ansible tasks that can:
     - Deploy a specific previous image tag.
     - Or revert `docker-compose.yml` to a previous version.
   - In CI/CD, expose an input (for `workflow_dispatch`) that takes a target image tag and triggers a rollback deployment.

4. **How does self-hosted runner improve security compared to GitHub-hosted?**  
   With a self-hosted runner:
   - All secrets and network access are confined to infrastructure you control.
   - No direct SSH from GitHub-hosted machines to your production network is needed.
   - You can restrict outbound traffic and lock down access to only your Ansible inventory hosts.
   - However, you must also secure and maintain the runner host itself (patching, access control, etc.).

---

## Task 5: Documentation (1 pt)

This file (`ansible/docs/LAB06.md`) serves as the main documentation artifact for Lab 6.

It includes:
- Overview of block/tag refactoring in `common` and `docker` roles.
- Docker Compose migration for the `web_app` role.
- Detailed wipe logic and safety mechanisms.
- Planned CI/CD workflow architecture and security considerations.
- Summaries of test runs and idempotency behaviour.

For full evidence (terminal outputs), see:
- `ansible-playbook playbooks/provision.yml --list-tags` — shows all tags (`common`, `docker`, `packages`, `users`, `docker_install`, `docker_config`).
- `ansible-playbook playbooks/deploy.yml` runs:
  - First run: creates compose project directory, templates file, deploys containers.
  - Second run: mostly `ok`, with Compose tasks sometimes reporting `changed`.
- Wipe scenarios:
  - Wipe only — containers and `/opt/devops-info-service` removed.
  - Clean reinstall — wipe followed by fresh deployment.
  - Safety scenario — `--tags web_app_wipe` without `web_app_wipe=true` does not execute wipe.

---

## Bonus Part 1: Multi-App (1.5 pts)

Not attempted yet. The current `web_app` role and Docker Compose setup are designed to be reusable for multiple apps by changing variables (`app_name`, `docker_image`, `app_port`, `compose_project_dir`), so extending to multi-app deployment would follow the pattern described in the lab (separate `vars` files and dedicated playbooks).

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

Not attempted yet. A natural extension would be:
- Either separate workflows for each app with path filters.
- Or a matrix-based workflow iterating over app/playbook combinations.

---

## Summary

- Implemented advanced Ansible role patterns using blocks, `rescue`/`always`, and a consistent tag strategy for `common` and `docker`.
- Migrated application deployment from raw `docker run` to declarative Docker Compose via the `web_app` role with role dependencies and idempotent behaviour.
- Added robust, double-gated wipe logic controlled by variable + tag and verified all four required scenarios.
- Designed a CI/CD workflow for Ansible using GitHub Actions, including linting, secure secret usage, deployment, and verification steps.
