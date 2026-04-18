# ConfigMaps and Persistent Volumes — Lab 12

This document describes the implementation of Lab 12 for `devops-info-service`: file-based configuration via ConfigMaps, environment configuration via ConfigMaps, and persistent visits counter storage via PVC.

---

## 1. Application changes

### Visits counter implementation

- The Python FastAPI service now stores request visits in a file: `/data/visits`.
- Every `GET /` request increments the counter and persists it.
- The app uses a mutex around file operations to avoid races under concurrent requests.
- Writes are atomic (`temp file -> rename`) to reduce corruption risk.

### New endpoint

- `GET /visits` returns:

```json
{
  "visits": 12
}
```

### Local Docker test (persistence)

`app_python/docker-compose.yml` mounts `./data:/data`, so counter state survives container restart.

Commands:

```bash
cd app_python
docker compose up --build -d
curl http://localhost:5000/
curl http://localhost:5000/
cat ./data/visits
docker compose down
docker compose up -d
curl http://localhost:5000/visits
```

Expected behavior: value from `./data/visits` is preserved after restart.

---

## 2. ConfigMap implementation

### 2.1 ConfigMap from file

- File: `k8s/devops-info-service/files/config.json`
- Template: `k8s/devops-info-service/templates/configmap-file.yaml`
- The template uses `.Files.Get` to inject JSON content into ConfigMap data.

### 2.2 ConfigMap for environment variables

- Template: `k8s/devops-info-service/templates/configmap-env.yaml`
- Injected keys:
  - `APP_NAME`
  - `APP_ENV`
  - `FEATURE_VISITS`
  - `LOG_LEVEL`

### 2.3 Deployment usage

- File ConfigMap is mounted as a volume at `/config`.
- Environment ConfigMap is injected using `envFrom.configMapRef`.
- Deployment also has checksum annotations to trigger rollout on ConfigMap changes.

Verification commands:

```bash
kubectl get configmap
POD=$(kubectl get pods -l app.kubernetes.io/name=devops-info-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- cat /config/config.json
kubectl exec "$POD" -- printenv | grep -E '^(APP_NAME|APP_ENV|FEATURE_VISITS|LOG_LEVEL)='
```

Example output:

```text
APP_NAME=devops-info-service
APP_ENV=dev
FEATURE_VISITS=true
LOG_LEVEL=info
```

---

## 3. Persistent Volume implementation

### 3.1 PVC configuration

- Template: `k8s/devops-info-service/templates/pvc.yaml`
- Access mode: `ReadWriteOnce`
- Requested size: `100Mi` (configurable in values)
- Storage class is configurable (`persistence.storageClass`)

### 3.2 Volume mount

- Deployment mounts PVC at `/data` (value: `persistence.mountPath`).
- Application uses `DATA_DIR=/data` and stores counter in `/data/visits`.

### 3.3 Persistence test evidence workflow

```bash
kubectl get pvc
POD=$(kubectl get pods -l app.kubernetes.io/name=devops-info-service -o jsonpath='{.items[0].metadata.name}')
curl http://<SERVICE_OR_NODEPORT>/
curl http://<SERVICE_OR_NODEPORT>/
kubectl exec "$POD" -- cat /data/visits
kubectl delete pod "$POD"
NEW_POD=$(kubectl get pods -l app.kubernetes.io/name=devops-info-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$NEW_POD" -- cat /data/visits
curl http://<SERVICE_OR_NODEPORT>/visits
```

Expected:
- Counter value before pod delete and after pod recreation is identical.
- `/visits` returns persisted value.

---

## 4. ConfigMap vs Secret

- Use **ConfigMap** for non-sensitive config:
  - app settings
  - feature flags
  - environment mode
- Use **Secret** for sensitive data:
  - passwords
  - API keys
  - tokens

Key differences:
- ConfigMap values are plain text in etcd (unless cluster-wide encryption is configured).
- Secret values are base64-encoded objects intended for confidential data handling and should be protected by RBAC and encryption-at-rest.

---

## 5. Required outputs checklist

Capture and attach these outputs/screenshots in your report:

1. `kubectl get configmap,pvc`
2. `kubectl exec <pod> -- cat /config/config.json`
3. `kubectl exec <pod> -- printenv | grep APP_`
4. Persistence test:
   - counter before pod deletion
   - `kubectl delete pod <pod-name>`
   - counter after new pod starts

---

## 5.1 Evidence from kind-lab12

Commands were executed against context `kind-lab12`.

`kubectl get configmap,pvc`:

```text
NAME                                               DATA   AGE
configmap/devops-info-devops-info-service-config   1      32s
configmap/devops-info-devops-info-service-env      4      32s
configmap/kube-root-ca.crt                         1      8m31s

NAME                                                         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-devops-info-service-data   Bound    pvc-4a3ded6a-ae38-442c-8c5b-ad59799bdffc   100Mi      RWO            standard       <unset>                 32s
```

`kubectl exec <pod> -- cat /config/config.json`:

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visitsCounter": true,
    "healthEndpoint": true
  },
  "settings": {
    "logLevel": "info",
    "timezone": "UTC"
  }
}
```

`kubectl exec <pod> -- printenv | grep APP_` (plus feature/log flags):

```text
APP_NAME=devops-info-service
LOG_LEVEL=info
APP_ENV=dev
FEATURE_VISITS=true
```

Persistence test:

```text
curl /visits before requests -> {"visits":0}
after two GET / requests     -> {"visits":2}
```

```text
pod_before=devops-info-devops-info-service-69fc954bf6-lgnbt
cat /data/visits -> 2
kubectl delete pod devops-info-devops-info-service-69fc954bf6-lgnbt
pod_after=devops-info-devops-info-service-69fc954bf6-lmh7j
cat /data/visits -> 2
curl /visits -> {"visits":2}
```

Result: visit counter value is preserved after pod deletion/recreation.

---

## 6. Bonus: ConfigMap hot reload (implemented pattern)

Implemented pattern: checksum annotations in Deployment pod template:

- `checksum/config-file`
- `checksum/config-env`

When ConfigMap content changes and Helm upgrade runs, checksums change, Pod template changes, and Deployment rolls pods automatically.

Notes:
- Directory ConfigMap mount updates automatically with kubelet delay.
- `subPath` should be avoided for hot updates because it does not receive live changes.
