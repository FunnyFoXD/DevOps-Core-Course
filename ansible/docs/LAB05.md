# Lab 5 — Ansible Fundamentals (Documentation)

## 1. Architecture Overview

- **Ansible version used:** ansible [core 2.16.3]
- **Target VM OS and version:** Ubuntu 22.04 LTS (kernel 5.15.0-170-generic, x86_64)
- **Role structure diagram or explanation:**
  - `ansible/` — project root
  - `inventory/hosts.ini` — static inventory (webservers group)
  - `roles/common` — base OS setup (apt, packages, timezone)
  - `roles/docker` — Docker installation and Python SDK for Ansible modules
  - `roles/app_deploy` — application deployment in a container
  - `playbooks/provision.yml` — provisioning playbook (common + docker)
  - `playbooks/deploy.yml` — application deployment playbook (app_deploy)
  - `group_vars/all.yml` — variables (including Vault-encrypted ones)
- **Why roles instead of monolithic playbooks?** Roles provide reusable logic, a clear structure, and separation of concerns; a single playbook stays small, and roles are easier to test and maintain.

---

## 2. Roles Documentation

### Role: common

- **Purpose:** Base server setup: update apt cache, install a set of packages (python3-pip, curl, git, vim, htop, ca-certificates, gnupg, unzip, jq), set timezone.
- **Variables:** `common_packages` (list of packages), `common_timezone` (default Europe/Moscow) — in `roles/common/defaults/main.yml`.
- **Handlers:** none.
- **Dependencies:** none.

### Role: docker

- **Purpose:** Install Docker: GPG key, Docker repository, packages docker-ce/docker-ce-cli/containerd.io, start and enable docker service, add user to docker group, install Python `docker` package for Ansible modules.
- **Variables:** `docker_group_user` (default `{{ ansible_user }}`), `docker_packages` — in `roles/docker/defaults/main.yml`.
- **Handlers:** `restart docker` — restart docker service.
- **Dependencies:** should run after common (requires ca-certificates, gnupg).

### Role: app_deploy

- **Purpose:** Deploy application in Docker: registry login (via `docker login` CLI), image pull, stop/remove old container, run new container with port mapping and restart policy, wait for port, verify `/health` endpoint. Uses Docker CLI (shell/command) instead of `community.docker` modules to avoid SDK connection issues on the target.
- **Variables:** from Vault (`group_vars/all.yml`): dockerhub_username, dockerhub_password, app_name, docker_image, app_port, etc.; in defaults: port, restart_policy, default environment variables.
- **Handlers:** restart app container (on image/config change).
- **Dependencies:** requires docker role (Docker must be installed on the host).

---

## 3. Idempotency Demonstration

### Terminal output from FIRST provision.yml run

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops-lab04-vm]

TASK [common : Update apt cache] ***********************************************
changed: [devops-lab04-vm]

TASK [common : Install common packages] ****************************************
changed: [devops-lab04-vm]

TASK [common : Set timezone] ***************************************************
changed: [devops-lab04-vm]

TASK [docker : Create apt keyrings directory] **********************************
ok: [devops-lab04-vm]

TASK [docker : Download Docker GPG key] ****************************************
changed: [devops-lab04-vm]

TASK [docker : Convert Docker GPG key to keyring format] ***********************
changed: [devops-lab04-vm]

TASK [docker : Add Docker APT repository] **************************************
changed: [devops-lab04-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [devops-lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [devops-lab04-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [devops-lab04-vm]

TASK [docker : Install Docker Python SDK for Ansible docker modules] ***********
changed: [devops-lab04-vm]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [devops-lab04-vm]

PLAY RECAP *********************************************************************
devops-lab04-vm            : ok=13   changed=10   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Terminal output from SECOND provision.yml run

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops-lab04-vm]

TASK [common : Update apt cache] ***********************************************
ok: [devops-lab04-vm]

TASK [common : Install common packages] ****************************************
ok: [devops-lab04-vm]

TASK [common : Set timezone] ***************************************************
ok: [devops-lab04-vm]

TASK [docker : Create apt keyrings directory] **********************************
ok: [devops-lab04-vm]

TASK [docker : Download Docker GPG key] ****************************************
ok: [devops-lab04-vm]

TASK [docker : Convert Docker GPG key to keyring format] ***********************
ok: [devops-lab04-vm]

TASK [docker : Add Docker APT repository] **************************************
ok: [devops-lab04-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [devops-lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [devops-lab04-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [devops-lab04-vm]

TASK [docker : Install Docker Python SDK for Ansible docker modules] ***********
ok: [devops-lab04-vm]

PLAY RECAP *********************************************************************
devops-lab04-vm            : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Analysis

- **What changed first time?** Apt cache update, common packages install, timezone change, Docker GPG key download, key conversion, Docker repo add, Docker packages install, user added to docker group, pip docker package install, handler restart docker ran.
- **What didn't change second time?** All tasks reported ok, changed=0 — desired state was already in place, no modifications made.

### Explanation: What makes your roles idempotent?

Stateful modules are used: `apt` with `state: present`, `service` with `state: started`, `file` with `state: directory`. They converge the system to a desired state instead of running one-off commands. A second run only checks state and does nothing if it already matches. Additionally: `cache_valid_time` for apt reduces unnecessary cache updates; `creates` on the shell task for gpg avoids re-running key conversion when the file already exists.

---

## 4. Ansible Vault Usage

- **How you store credentials securely:** Credentials (Docker Hub login/password, image tags, etc.) are stored in `group_vars/all.yml`, encrypted with `ansible-vault create` / `ansible-vault edit`. The file can be committed to the repo.
- **Vault password management strategy:** Run with password prompt: `ansible-playbook playbook.yml --ask-vault-pass`. Alternatively use a password file (e.g. `.vault_pass`) set in `ansible.cfg` as `vault_password_file`; the password file must be in `.gitignore`.
- **Example of encrypted file (show it's encrypted!):**

  The file is created with `ansible-vault create group_vars/all.yml`. When encrypted, the start of the file looks like:

  ```
  $ANSIBLE_VAULT;1.1;AES256
  663864396537323832336234...
  ```

  (followed by a base64-like string). To verify: `head -3 group_vars/all.yml`.

- **Why Ansible Vault is important:** Secrets are not stored in plain text in the repo; the encrypted file can be committed safely and passwords do not need to be passed separately on every run.

---

## 5. Deployment Verification

- **Terminal output from deploy.yml run:**

  ```
  PLAY [Deploy application] **********************************************************

  TASK [Gathering Facts] *************************************************************
  ok: [devops-lab04-vm]

  TASK [app_deploy : Ensure Docker Python SDK >= 7.0 (fix http+docker scheme)] *******
  ok: [devops-lab04-vm]

  TASK [app_deploy : Log in to Docker Hub (via CLI to avoid SDK connection issues)] ***
  changed: [devops-lab04-vm]

  TASK [app_deploy : Pull Docker image] **********************************************
  changed: [devops-lab04-vm]

  TASK [app_deploy : Stop and remove existing container] *****************************
  changed: [devops-lab04-vm]

  TASK [app_deploy : Run application container] **************************************
  changed: [devops-lab04-vm]

  TASK [app_deploy : Wait for application port] **************************************
  ok: [devops-lab04-vm]

  TASK [app_deploy : Verify health endpoint] *****************************************
  ok: [devops-lab04-vm]

  PLAY RECAP *********************************************************************
  devops-lab04-vm            : ok=8    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
  ```

- **Container status (`docker ps` output):**

  Run: `ansible webservers -a "docker ps" --ask-vault-pass`

  ```
  devops-lab04-vm | CHANGED | rc=0 >>
  CONTAINER ID   IMAGE                                   COMMAND           CREATED              STATUS              PORTS                                         NAMES
  5e3199f40a00   funnyfoxd/devops-info-service:2026.02   "python app.py"   About a minute ago   Up About a minute   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   devops-info-service
  ```

- **Health check verification (`curl` outputs):**

  `curl http://89.169.156.227:5000/health`:
  ```json
  {"status":"healthy","timestamp":"2026-02-25T16:07:31.328895+00:00","uptime_seconds":...}
  ```

  `curl http://89.169.156.227:5000/`:
  ```json
  {"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"5e3199f40a00","platform":"Linux",...},"runtime":{"uptime_seconds":47,...},"request":{...},"endpoints":[...]}
  ```

- **Handler execution (if any):** The app_deploy role uses Docker CLI (shell) for login, pull, and run; no handlers run during a normal deploy. The handler "restart app container" is available for use with `notify` if needed (e.g. when reusing community.docker tasks in the future).

---

## 6. Key Decisions

- **Why use roles instead of plain playbooks?** Roles give a clear structure, reuse, and separation by concern (common / docker / app); define a role once and use it across playbooks and projects.
- **How do roles improve reusability?** The same role (e.g. docker or common) can be used in multiple playbooks and host groups without duplicating tasks.
- **What makes a task idempotent?** A task is idempotent when the module describes the desired state (present, started, directory, etc.) rather than a one-off command; a second run makes no changes if the state already matches.
- **How do handlers improve efficiency?** Handlers run once at the end of the play after all changed tasks; e.g. a single service restart instead of several when many tasks change.
- **Why is Ansible Vault necessary?** To store passwords and tokens in the repo in encrypted form and avoid exposing them in logs and code.

---

## 7. Challenges

- The timezone module required the `community.general` collection — added `requirements.yml` and install via `ansible-galaxy collection install -r requirements.yml`.
- Docker installation follows the official approach: key in keyring (`/etc/apt/keyrings`) instead of deprecated `apt_key`; the key conversion task uses `creates` so `gpg --dearmor` is not run on every playbook run.
- **Docker Python SDK on target:** `community.docker.docker_login` and `docker_image`/`docker_container` failed with "Not supported URL scheme http+docker" on the remote host (despite `docker>=7.0.0`). The app_deploy role was switched to Docker CLI (`docker login`, `docker pull`, `docker run`) so deployment does not depend on the SDK for these steps.
- **Vault and ad-hoc:** Any command run from the `ansible/` directory loads `group_vars/all.yml`; when it is encrypted, use `--ask-vault-pass` even for ad-hoc (e.g. `ansible webservers -a "docker ps" --ask-vault-pass`).
