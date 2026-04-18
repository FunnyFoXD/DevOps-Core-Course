# Secret management — Lab 11

This document describes Kubernetes Secrets, Helm-managed credentials, resource limits, and optional HashiCorp Vault Agent injection for the `devops-info-service` chart. It includes **evidence** from a local **kind** cluster (`kind-lab11`, context `kind-lab11`).

---

## 1. Kubernetes Secrets (Task 1)

### Creating `app-credentials` with kubectl

Use literals (replace values in your shell; do not commit real credentials):

```bash
kubectl --context kind-lab11 create secret generic app-credentials \
  --from-literal=username=lab11-user \
  --from-literal=password=lab11-secret-demo
```

### Viewing and decoding

```bash
kubectl --context kind-lab11 get secret app-credentials -o yaml
```

**Evidence (`kubectl get secret app-credentials -o yaml`, fragment):** keys in `data:` are **base64-encoded** (not encrypted).

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
data:
  password: bGFiMTEtc2VjcmV0LWRlbW8=
  username: bGFiMTEtdXNlcg==
```

Decode locally (GNU `base64` on Linux: `-d`; on macOS: `-D`):

```bash
kubectl --context kind-lab11 get secret app-credentials -o jsonpath='{.data.username}' | base64 -d   # or: base64 -D
echo
kubectl --context kind-lab11 get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
echo
```

**Decoded demonstration (same cluster):** `lab11-user` and `lab11-secret-demo`.

### Base64 encoding vs encryption

- **Base64** is reversible encoding for transporting binary data as text. Anyone who can read the Secret object through the API (or etcd, depending on cluster hardening) can decode it.
- **Encryption** uses keys and aims for confidentiality even if storage is exposed. That is **not** what base64 provides.

### Security implications (at rest and etcd)

- By default, Kubernetes **does not encrypt Secret values at rest** in etcd unless you configure **encryption at rest** (a `EncryptionConfiguration` with providers such as `aescbc`, `secretbox`, or KMS).
- **etcd encryption** should be enabled when you need defense in depth: compromised etcd backups or disk should not trivially reveal Secret payloads. Combine with strict **RBAC**, audit logging, and external secret managers for production.

References: [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/), [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/).

---

## 2. Helm secret integration (Task 2)

### Chart structure

- Secret template: [`devops-info-service/templates/secrets.yaml`](devops-info-service/templates/secrets.yaml) — creates an `Opaque` Secret when `secrets.enabled` is true, using `stringData` so Helm stores plain literals in the chart values while Kubernetes stores encoded data.
- Default placeholders: [`devops-info-service/values.yaml`](devops-info-service/values.yaml) under `secrets:` (`username` / `password`). Override at install time with `--set` or a private values file **not** committed to Git.

### How the workload consumes the Secret

[`devops-info-service/templates/rollout.yaml`](devops-info-service/templates/rollout.yaml) (Argo Rollouts `Rollout`; Lab 14) uses `envFrom` with `secretRef` so **all keys** from the chart Secret are exposed as environment variables:

```yaml
envFrom:
  - secretRef:
      name: <release>-devops-info-service-secret
```

Non-sensitive configuration remains in explicit `env` entries, centralized in a named template for reuse (see §6).

### Verification (without printing secret values)

The chart Secret keys are `username` and `password`; with `envFrom` / `secretRef`, Kubernetes exposes them as environment variables **`username`** and **`password`** (same spelling as the keys), not `USERNAME` / `PASSWORD`.

Deploy the chart:

```bash
helm upgrade --install devops-info ./k8s/devops-info-service \
  --kube-context kind-lab11 \
  --namespace default \
  --create-namespace
```

Redact values but confirm names:

```bash
POD=$(kubectl --context kind-lab11 get pods -l app.kubernetes.io/name=devops-info-service -o jsonpath='{.items[0].metadata.name}')
kubectl --context kind-lab11 exec "$POD" -c devops-info-service -- env | sort | grep -E '^(username|password)=' | sed 's/=.*/=<redacted>/'
```

Or only check presence:

```bash
kubectl --context kind-lab11 exec "$POD" -c devops-info-service -- sh -c 'test -n "$username" && echo username is set'
kubectl --context kind-lab11 exec "$POD" -c devops-info-service -- sh -c 'test -n "$password" && echo password is set'
```

**Evidence:** both variables were set; chart defaults were `changeme-user` / `changeme-password` until overridden with `--set secrets.*`.

`kubectl describe pod` shows **that** a Secret is referenced (e.g. `devops-info-devops-info-service-secret`), not the secret **data** — values do not appear in describe output.

---

## 3. Resource management (Task 2)

### Configuration

CPU and memory **requests** and **limits** are defined under `resources` in [`values.yaml`](devops-info-service/values.yaml). Environment-specific files ([`values-dev.yaml`](devops-info-service/values-dev.yaml), [`values-prod.yaml`](devops-info-service/values-prod.yaml)) override them for smaller dev pods or larger production pods.

### Requests vs limits

- **Requests**: scheduler uses them to place the pod on a node with enough allocatable resources; kubelet uses them for `QoS` and (with cgroups) guaranteed minimums for CPU shares and memory.
- **Limits**: hard cap; CPU may be throttled, memory over-limit leads to OOM kill.

### Choosing values

Start from observed usage (`kubectl top pod` if metrics-server is installed), leave headroom for spikes, and align with SLOs. Dev clusters can use low requests/limits; production typically sets requests close to steady-state usage and limits above peak.

**Defaults in this chart** ([`values.yaml`](devops-info-service/values.yaml)): requests `cpu: 100m`, `memory: 128Mi`; limits `cpu: 200m`, `memory: 256Mi`. [`values-dev.yaml`](devops-info-service/values-dev.yaml) / [`values-prod.yaml`](devops-info-service/values-prod.yaml) override these for smaller dev or larger prod workloads.

---

## 4. HashiCorp Vault integration (Task 3)

### Install Vault (dev mode, learning only)

Preferred (official repo):

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault --kube-context kind-lab11 \
  --set 'server.dev.enabled=true' \
  --set 'injector.enabled=true'
```

**If `helm repo add` / `helm install` fails with HTTP 403** (e.g. CloudFront/geo), install the same chart from the [vault-helm GitHub release](https://github.com/hashicorp/vault-helm/releases) tarball:

```bash
curl -sL "https://api.github.com/repos/hashicorp/vault-helm/tarball/v0.32.0" -o /tmp/vault-helm.tgz
mkdir -p /tmp/vault-helm && tar -xzf /tmp/vault-helm.tgz -C /tmp/vault-helm
CHART_DIR=$(find /tmp/vault-helm -maxdepth 1 -type d -name 'hashicorp-vault-helm-*' | head -1)

helm install vault "$CHART_DIR" --kube-context kind-lab11 \
  --set 'server.dev.enabled=true' \
  --set 'injector.enabled=true' \
  --wait --timeout 6m
```

Verify:

```bash
kubectl --context kind-lab11 get pods -l app.kubernetes.io/name=vault
```

**Evidence:**

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          ...
vault-agent-injector-...                1/1     Running   0          ...
```

### Configure Vault (inside `vault-0`)

Dev mode uses root token **`root`** and `VAULT_ADDR=http://127.0.0.1:8200` inside the pod. Example one-shot setup:

```bash
kubectl --context kind-lab11 exec vault-0 -- sh -ec '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
vault secrets enable -path=secret kv-v2 2>/dev/null || true
vault kv put secret/devops-info/config username="vault-demo-user" password="vault-demo-pass"
vault auth enable kubernetes 2>/dev/null || true
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443" \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
'
```

### Policy and role (sanitized; matches KV v2)

KV v2 reads use the `secret/data/...` path; listing often needs `secret/metadata/...`:

```hcl
path "secret/data/devops-info/*" {
  capabilities = ["read"]
}
path "secret/metadata/devops-info/*" {
  capabilities = ["list", "read"]
}
```

```bash
kubectl --context kind-lab11 exec vault-0 -- sh -ec '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
vault policy write devops-info-service - <<EOF
path "secret/data/devops-info/*" {
  capabilities = ["read"]
}
path "secret/metadata/devops-info/*" {
  capabilities = ["list", "read"]
}
EOF
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=devops-info-devops-info-service \
  bound_service_account_namespaces=default \
  policies=devops-info-service \
  ttl=1h
'
```

Adjust `bound_service_account_names` to match Helm: with release name `devops-info` and chart name `devops-info-service`, the ServiceAccount is typically **`devops-info-devops-info-service`** in the release namespace.

### Agent injection in this chart

When `vault.enabled` is true, the pod template receives annotations such as:

- `vault.hashicorp.com/agent-inject: "true"`
- `vault.hashicorp.com/role`: must match the Vault role above
- `vault.hashicorp.com/agent-inject-secret-config`: KV v2 path, e.g. `secret/data/devops-info/config`

The injector mounts files under `/vault/secrets/` (e.g. `/vault/secrets/config` for the `config` suffix).

Enable on upgrade (with Vault):

```bash
helm upgrade --install devops-info ./k8s/devops-info-service \
  --kube-context kind-lab11 \
  --namespace default \
  --set vault.enabled=true \
  --set vault.role=devops-info-service \
  --set replicaCount=1
```

**Evidence:** application pod **2/2** (app container + `vault-agent` sidecar), annotations include `vault.hashicorp.com/agent-inject: true` and `vault.hashicorp.com/role: devops-info-service`.

Proof inside the pod (container `devops-info-service`):

```bash
POD=$(kubectl --context kind-lab11 get pods -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl --context kind-lab11 exec "$POD" -c devops-info-service -- ls -la /vault/secrets
kubectl --context kind-lab11 exec "$POD" -c devops-info-service -- sh -c 'test -f /vault/secrets/config && echo file present'
```

**Evidence:** `/vault/secrets/config` exists; injector renders KV payload (structure similar to `data: map[password:... username:...]` plus metadata — redact before committing real clusters).

**`kubectl describe pod` (fragment)** — shows Secret **reference** and Vault annotations, not secret values:

```text
Annotations:      vault.hashicorp.com/agent-inject: true
                  vault.hashicorp.com/agent-inject-secret-config: secret/data/devops-info/config
                  vault.hashicorp.com/role: devops-info-service
...
    Environment Variables from:
      devops-info-devops-info-service-secret  Secret  Optional: false
```

### Sidecar injection pattern

The **Vault Agent Injector** mutates the pod spec: it adds an init container and sidecar that authenticate to Vault (here via Kubernetes auth), fetch secrets, and write them to a shared volume. The application container reads files without embedding credentials in the image or Helm values.

---

## 5. Security analysis

| Aspect | Native Kubernetes Secret | Vault (Agent injection) |
|--------|-------------------------|-------------------------|
| Storage | API object in etcd (encode + optional etcd encryption) | Secrets in Vault; pod gets short-lived lease / rendered files |
| Rotation | Manual or external automation | Central rotation; agent can renew / re-render (see bonus) |
| Access control | RBAC on Secret objects | Vault policies + K8s auth binding |
| Best for | Simple apps, bootstrap, low sensitivity | Centralized policies, audit, dynamic secrets, many clusters |

**Production recommendations**: enable **etcd encryption at rest**, narrow RBAC, avoid committing real values, prefer **external** managers (Vault, cloud secret stores) for high-sensitivity data, and run Vault in **HA** with proper auto-unseal (not dev mode).

---

## 6. Bonus — Vault Agent templates and Helm DRY (Bonus task)

### Template annotation (implementation)

When `vault.enabled` and `vault.template.enabled` are true, the chart adds `vault.hashicorp.com/agent-inject-template-appconfig`. The annotation value is the **Vault Agent** template (Go template + `secret` function), read from [`values.yaml`](devops-info-service/values.yaml) as `vault.template.body`. Helm only passes the string through; it does not evaluate `{{- with secret ... }}` itself.

Rendering in the chart template:

```24:27:k8s/devops-info-service/templates/rollout.yaml
        {{- if .Values.vault.template.enabled }}
        vault.hashicorp.com/agent-inject-template-appconfig: |
{{ .Values.vault.template.body | trim | nindent 10 }}
        {{- end }}
```

Default body in `values.yaml` pulls **two fields** from the same KV v2 path and writes them into **one** file in pseudo-`.env` form (`USERNAME=...`, `PASSWORD=...`), satisfying the “multiple secrets in one rendered file” idea at the application-path level.

### Enable on the cluster (kind-lab11)

```bash
helm upgrade --install devops-info ./k8s/devops-info-service \
  --kube-context kind-lab11 \
  --namespace default \
  --set vault.enabled=true \
  --set vault.role=devops-info-service \
  --set vault.template.enabled=true \
  --set replicaCount=1 \
  --wait --timeout 5m
```

After rollout, the pod has **both** the standard injected file (`agent-inject-secret-config` -> `/vault/secrets/config`) and the **templated** file (`agent-inject-template-appconfig` -> `/vault/secrets/appconfig`).

### Evidence — annotations and files

`kubectl describe pod` (keys only; template body is long):

```text
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-secret-config: secret/data/devops-info/config
  vault.hashicorp.com/agent-inject-template-appconfig: |
    {{- with secret "secret/data/devops-info/config" -}}
    USERNAME={{ .Data.data.username }}
    PASSWORD={{ .Data.data.password }}
    {{- end -}}
  vault.hashicorp.com/role: devops-info-service
```

Directory inside the **app** container (`-c devops-info-service`):

```text
$ kubectl --context kind-lab11 exec "$POD" -c devops-info-service -- ls -la /vault/secrets
total 12
drwxrwxrwt 2 root root   80 ... .
drwxr-xr-x 3 root root 4096 ... ..
-rw-r--r-- 1 100 appuser   49 ... appconfig
-rw-r--r-- 1 100 appuser  183 ... config
```

**Rendered `appconfig`** (values match the **demo** KV entry from §4 on the learning cluster; replace with `<redacted>` in real submissions if your cluster used real credentials):

```text
$ kubectl --context kind-lab11 exec "$POD" -c devops-info-service -- cat /vault/secrets/appconfig
USERNAME=vault-demo-user
PASSWORD=vault-demo-pass
```

Compared to the raw `config` file from `agent-inject-secret-config`, the templated file is a **custom layout** suitable for dotenv-style loaders or scripts.

### Dynamic refresh and `agent-inject-command`

Vault Agent can **renew** leases and **re-render** files when static secret versions change (depending on backend and agent config). The app still needs a **reload signal** if it only reads the file at startup. The annotation [`vault.hashicorp.com/agent-inject-command`](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations) runs a command after an update (for example touching a file or sending `SIGHUP`), so the process can pick up new materialized secrets without replacing the pod.

### Named Helm template (DRY env block)

Shared non-secret environment variables are defined once and included from the Rollout pod template:

```49:55:k8s/devops-info-service/templates/_helpers.tpl
{{/* Common non-secret container environment variables (DRY for deployment) */}}
{{- define "devops-info-service.containerEnv" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
{{- end }}
```

```44:45:k8s/devops-info-service/templates/rollout.yaml
          env:
            {{- include "devops-info-service.containerEnv" . | nindent 12 }}
```

**Benefit:** any future template (e.g. a Job) can reuse `include "devops-info-service.containerEnv" .` instead of duplicating `HOST` / `PORT` blocks.

---

## 7. Checklist mapping
All tasks are done
