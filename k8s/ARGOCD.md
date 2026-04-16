# Lab 13 — GitOps with ArgoCD (Report)

This lab deploys the existing Helm chart (`k8s/devops-info-service`) via ArgoCD as the single source of truth (GitOps).

## 1) ArgoCD Setup

### Install via Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd

kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

### Access UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Get the initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

Login:
- URL: `https://localhost:8080`
- Username: `admin`
- Password: from the command above

### Install & configure CLI

```bash
# macOS
brew install argocd

argocd login localhost:8080 --insecure
argocd version
argocd app list
```

### Evidence (screenshots)

- [ ] ArgoCD UI main screen
- [ ] Settings / clusters / projects view (any relevant screen)

## 2) Application configuration (single environment)

### Manifest

Application manifest is stored in `k8s/argocd/application.yaml`.

Key settings:
- Source repo: `https://github.com/FunnyFoXD/DevOps-Core-Course.git`
- Revision: `lab13`
- Chart path: `k8s/devops-info-service`
- Values: `values.yaml`
- Destination namespace: `default`
- Sync: manual

### Deploy & sync

```bash
kubectl apply -f k8s/argocd/application.yaml

argocd app get devops-info-service
argocd app sync devops-info-service
```

### Evidence

- [ ] Application created and visible in UI
- [ ] Sync succeeded, app is Healthy

## 3) Multi-environment (dev/prod)

### Namespaces

ArgoCD manifests include `CreateNamespace=true`, but you can also create namespaces explicitly:

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Environment-specific Applications

Manifests are stored in `k8s/argocd/`:
- `application-dev.yaml` uses `values-dev.yaml` and deploys to namespace `dev`
- `application-prod.yaml` uses `values-prod.yaml` and deploys to namespace `prod`

Apply:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml

argocd app list
```

### Sync policy differences and rationale

- Dev (`devops-info-service-dev`): **auto-sync enabled**
  - `selfHeal: true`: revert out-of-band cluster changes back to Git state
  - `prune: true`: delete resources removed from Git
  - Rationale: fast feedback, continuous delivery, safe to auto-correct drift

- Prod (`devops-info-service-prod`): **manual sync**
  - No `automated` block
  - Rationale: change review, controlled rollout timing, safer operations and compliance needs

### Verification

```bash
kubectl get all -n dev
kubectl get all -n prod

argocd app get devops-info-service-dev
argocd app get devops-info-service-prod
```

### Evidence (screenshots)

- [ ] ArgoCD UI shows both `devops-info-service-dev` and `devops-info-service-prod`
- [ ] Different replica counts/resources applied (from `values-dev.yaml` vs `values-prod.yaml`)

## 4) Self-healing & drift tests (dev)

### 4.1 Manual scale drift (ArgoCD self-heal)

1) Record current state:

```bash
kubectl get deploy -n dev
argocd app get devops-info-service-dev
```

2) Create drift:

```bash
kubectl scale deployment -n dev -l app.kubernetes.io/instance=devops-info-service-dev --replicas=5
```

3) Observe revert:

```bash
kubectl get pods -n dev -w
argocd app diff devops-info-service-dev
```

Fill in evidence (timestamps):
- Before scale: `__ : __`
- After scale: `__ : __`
- Reverted by ArgoCD: `__ : __`

### 4.2 Pod deletion (Kubernetes self-heal)

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=devops-info-service-dev
kubectl get pods -n dev -w
```

Notes:
- Kubernetes recreates pods to satisfy Deployment/ReplicaSet desired state.
- This is **not** ArgoCD drift correction; it’s Kubernetes controller behavior.

### 4.3 Configuration drift (ArgoCD diff + self-heal)

Example: add a label to the Deployment:

```bash
kubectl label deployment -n dev -l app.kubernetes.io/instance=devops-info-service-dev lab13-drift=true --overwrite
argocd app diff devops-info-service-dev
```

With `selfHeal: true`, ArgoCD should revert the change back to Git-defined manifests.

### 4.4 When does ArgoCD sync vs Kubernetes heals?

- Kubernetes heals when: a managed object (like a Pod) disappears or diverges from its controller’s desired state.
- ArgoCD syncs when: Git desired state differs from the live cluster state (drift), on polling interval or via webhooks/manual sync.

Default Git polling interval (typical): ~3 minutes (can vary by config).

## Bonus — ApplicationSet

To generate both environments from a single declarative resource, `k8s/argocd/applicationset.yaml` uses a **List generator** with `goTemplate` enabled.

Apply:

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```

Notes:
- It generates `devops-info-service-set-dev` and `devops-info-service-set-prod`.
- Dev gets `automated` sync policy (auto-sync + prune + self-heal).
- Prod stays manual (no `automated` block).

## 5) Screenshots checklist

- [ ] ArgoCD UI: apps list with both environments
- [ ] One app details screen showing Sync/Health
- [ ] Diff view for a drift test

