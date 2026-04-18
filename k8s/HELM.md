# Helm Implementation Report (Lab 10)

Lab 11 extends this chart with Kubernetes Secrets, resource tuning, and optional Vault Agent injection — see **[`SECRETS.md`](SECRETS.md)**.

## 1) Chart Overview

Helm chart is implemented in `k8s/devops-info-service` and replaces Lab 9 static manifests with reusable templates.

Main chart files:

- `Chart.yaml` - chart metadata and versioning
- `values.yaml` - baseline values (replicas, image, service, resources, probes, hooks, secrets, vault)
- `values-dev.yaml` - development overrides
- `values-prod.yaml` - production overrides
- `templates/rollout.yaml` - Argo Rollouts `Rollout` (Lab 14; replaces Deployment)
- `templates/secrets.yaml` - optional Helm-managed Secret (Lab 11)
- `templates/serviceaccount.yaml` - workload ServiceAccount (Vault K8s auth, Lab 11)
- `templates/service.yaml` - Service template
- `templates/_helpers.tpl` - naming, labels, shared `env` partial (Lab 11)
- `templates/hooks/pre-install-job.yaml` - pre-install hook job
- `templates/hooks/post-install-job.yaml` - post-install hook job

Values are grouped by concern (`image`, `service`, `resources`, `livenessProbe`, `readinessProbe`, `hooks`) to keep configuration predictable and environment-friendly.

## 2) Configuration Guide

Important configurable values:

- `replicaCount`
- `image.repository`, `image.tag`, `image.pullPolicy`
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`
- `resources.requests`, `resources.limits`
- `livenessProbe`, `readinessProbe` (kept enabled and configurable)
- `hooks.image`, `hooks.preInstall.*`, `hooks.postInstall.*`
- `secrets.*`, `serviceAccount.*`, `vault.*`, `podAnnotations` (Lab 11 — details in `SECRETS.md`)

Environment files:

- `values-dev.yaml`: 1 replica, smaller resources, NodePort, fast startup probes
- `values-prod.yaml`: 5 replicas, stronger resources, LoadBalancer-ready, stricter timings

Install examples:

```bash
# default
helm install myrelease k8s/devops-info-service

# dev
helm install myrelease-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# prod
helm install myrelease-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

## 3) Hook Implementation

Implemented lifecycle hooks:

- Pre-install job:
  - `helm.sh/hook: pre-install`
  - `helm.sh/hook-weight: "-5"`
- Post-install job:
  - `helm.sh/hook: post-install`
  - `helm.sh/hook-weight: "5"`

Deletion policy on both hooks:

- `helm.sh/hook-delete-policy: hook-succeeded`

This keeps cluster clean after successful hook execution.

## 4) Installation Evidence

### Helm installed and verified (4.x)

```text
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Public chart exploration

```text
$ helm show chart oci://registry-1.docker.io/bitnamicharts/nginx
Pulled: registry-1.docker.io/bitnamicharts/nginx:22.6.10
Digest: sha256:d5095131fcc79a343c83f7f826fe0e7f70a797bc9c8f47ed8e9e0cff5c4cf62c
apiVersion: v2
name: nginx
version: 22.6.10
appVersion: 1.29.7
dependencies:
- name: common
  repository: oci://registry-1.docker.io/bitnamicharts
```

### kind cluster evidence

```text
$ kubectl cluster-info --context kind-lab10
Kubernetes control plane is running at https://127.0.0.1:54230
CoreDNS is running at https://127.0.0.1:54230/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes -o wide
NAME                  STATUS   ROLES           AGE   VERSION   INTERNAL-IP
lab10-control-plane   Ready    control-plane   ...   v1.35.0   172.18.0.2
```

### Release install and upgrade evidence

Development install:

```text
$ helm install myrelease-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
NAME: myrelease-dev
STATUS: deployed
REVISION: 1
```

Production upgrade (same release):

```text
$ helm upgrade myrelease-dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
STATUS: deployed
REVISION: 4
```

`helm list`:

```text
NAME          NAMESPACE REVISION STATUS   CHART                     APP VERSION
myrelease-dev default   4        deployed devops-info-service-0.1.0 lab02
```

`kubectl get all` (after prod upgrade):

```text
NAME                                                     READY   STATUS    AGE
pod/myrelease-dev-devops-info-service-78ddc5568d-9hz4f   1/1     Running   ...
pod/myrelease-dev-devops-info-service-78ddc5568d-jcgjk   1/1     Running   ...
pod/myrelease-dev-devops-info-service-78ddc5568d-kgtk7   1/1     Running   ...
pod/myrelease-dev-devops-info-service-78ddc5568d-pm2bw   1/1     Running   ...
pod/myrelease-dev-devops-info-service-78ddc5568d-xbsdz   1/1     Running   ...

NAME                                        TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)
service/myrelease-dev-devops-info-service   LoadBalancer   10.96.96.106   <pending>     80:30080/TCP

NAME                                                READY   UP-TO-DATE   AVAILABLE
deployment.apps/myrelease-dev-devops-info-service   5/5     5            5
```

Hook evidence:

```text
$ helm get hooks myrelease-dev
... "helm.sh/hook": post-install
... "helm.sh/hook-weight": "5"
... "helm.sh/hook-delete-policy": hook-succeeded
... "helm.sh/hook": pre-install
... "helm.sh/hook-weight": "-5"
... "helm.sh/hook-delete-policy": hook-succeeded

$ kubectl get jobs -A
No resources found
```

`kubectl get jobs -A` returning no resources is expected due `hook-succeeded` deletion policy.

### Dev vs Prod differences verified

- Dev: `replicaCount=1`, `service.type=NodePort`
- Prod: `replicaCount=5`, `service.type=LoadBalancer`
- Changes applied through `helm upgrade` and confirmed by deployment/service outputs.

## 5) Operations

```bash
# install
helm install myrelease k8s/devops-info-service

# upgrade (prod)
helm upgrade myrelease k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# rollback
helm rollback myrelease 1

# uninstall
helm uninstall myrelease
```

## 6) Testing & Validation

Lint:

```text
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

Template rendering:

```bash
helm template test-release k8s/devops-info-service
helm template test-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
helm template test-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

Dry-run:

```bash
helm install --dry-run --debug demo-release k8s/devops-info-service
```

Accessibility check pattern:

```bash
kubectl get svc
curl http://<node-ip>:<nodeport>/health
```

Note: for runtime cluster proof in this session, install/upgrade used explicit overrides to a public test image (`nginx`) so Pods become healthy in kind without private registry/image pull issues.

## Helm Value Proposition

Helm packages Kubernetes resources into versioned, reusable charts, supports environment-based configuration via values files, and provides reliable lifecycle operations (install/upgrade/rollback/uninstall) with optional hooks for automation.
