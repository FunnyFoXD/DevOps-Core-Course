# Kubernetes Deployment Report (Lab 9)

## Lab 11 — Secrets and Vault

Lab 11 (Kubernetes Secrets + Helm secrets + HashiCorp Vault Agent injection) is documented in **[`k8s/SECRETS.md`](SECRETS.md)**. There you will find:

- imperative `kubectl` Secret create / view / base64 decode (with **kind-lab11** evidence);
- Helm chart pieces: [`devops-info-service/templates/secrets.yaml`](devops-info-service/templates/secrets.yaml), `envFrom` in [`rollout.yaml`](devops-info-service/templates/rollout.yaml), resource limits in [`values.yaml`](devops-info-service/values.yaml);
- Vault install (official Helm repo **or** GitHub tarball if the repo returns 403), KV v2, Kubernetes auth, policy/role, injector proof under `/vault/secrets/`;
- bonus (**`SECRETS.md` §6**): `agent-inject-template-appconfig`, rendered `/vault/secrets/appconfig` (kind-lab11 evidence), refresh / `agent-inject-command`, named Helm env template in [`_helpers.tpl`](devops-info-service/templates/_helpers.tpl).

Helm chart path: [`k8s/devops-info-service/`](devops-info-service/). Lab 10 write-up (if present): [`k8s/HELM.md`](HELM.md).

---

## Architecture Overview
We deployed the Lab 2 Python FastAPI app (`funnyfoxd/devops-info-service:lab02`) to Kubernetes using declarative manifests.

Simplified flow:

```
Client (host)
   |
   |  (NodePort: 30080)
   v
K8s Node (INTERNAL-IP, e.g. 192.168.0.3)
   |
   |  kube-proxy forwards to matching Pods
   v
Service: devops-info-service (selector: app=devops-info-service)
   |
   v
Pods (managed by Deployment / ReplicaSet)
   |
   v
Container listens on :5000
```

Resources strategy:
- CPU/memory requests and limits are defined to help scheduling and protect cluster stability.
- Requests: `cpu=100m`, `memory=128Mi`
- Limits: `cpu=200m`, `memory=256Mi`

Health strategy:
- `readinessProbe` and `livenessProbe` are HTTP GET checks against `/health`.
- `readinessProbe` controls when Pods receive traffic.
- `livenessProbe` restarts a container if it becomes unhealthy.

Chosen local cluster tool:
- `kind` (Kubernetes in Docker) because it is lightweight and works well for local learning/development.

## Manifest Files
### `k8s/deployment.yml`
- Defines `Deployment` named `devops-info-service`
- Labels:
  - `app: devops-info-service` for organization and selectors
- Deployment settings:
  - Initial `replicas: 3`
  - `strategy: RollingUpdate` with:
    - `maxSurge: 1`
    - `maxUnavailable: 0` (aims to keep availability during updates)
- Container:
  - Image: `funnyfoxd/devops-info-service:lab02`
  - Container port: `5000`
  - Env:
    - `HOST=0.0.0.0`
    - `PORT=5000`
  - Probes:
    - `livenessProbe` -> `GET /health` on port `5000`
    - `readinessProbe` -> `GET /health` on port `5000`
  - Resources (requests/limits) set as described in the Architecture section

### `k8s/service.yml`
- Defines `Service` named `devops-info-service`
- Type: `NodePort`
- Selector: `app=devops-info-service` (must match Deployment Pod labels)
- Ports:
  - Service port: `80`
  - targetPort: `5000`
  - nodePort: `30080`

## Deployment Evidence
### Cluster setup (Task 1)
`kubectl cluster-info`:
```text
Kubernetes control plane is running at https://127.0.0.1:45499
CoreDNS is running at https://127.0.0.1:45499/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

`kubectl get nodes -o wide`:
```text
NAME                       STATUS   ROLES           AGE     VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION      CONTAINER-RUNTIME
lab09-kind-control-plane   Ready    control-plane   5m24s   v1.27.3   192.168.0.3   <none>        Debian GNU/Linux 11 (bullseye)   6.17.0-19-generic   containerd://1.7.1
```

### Kubernetes resources (Task 5)
`kubectl get pods,svc -o wide`:
```text
NAME                                       READY   STATUS    RESTARTS   AGE   IP            NODE                       NOMINATED NODE   READINESS GATES
pod/devops-info-service-69979f8f89-794fn   1/1     Running   0          53s   10.244.0.15   lab09-kind-control-plane   <none>           <none>
pod/devops-info-service-69979f8f89-mj9tb   1/1     Running   0          68s   10.244.0.13   lab09-kind-control-plane   <none>           <none>
pod/devops-info-service-69979f8f89-t2kwf   1/1     Running   0          63s   10.244.0.14   lab09-kind-control-plane   <none>           <none>

NAME                          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service   NodePort    10.96.75.60   <none>        80:30080/TCP   3m17s   app=devops-info-service
service/kubernetes            ClusterIP   10.96.0.1     <none>        443/TCP        5m26s   <none>
```

`kubectl get all -o wide`:
```text
NAME                                       READY   STATUS    RESTARTS   AGE   IP            NODE                       NOMINATED NODE   READINESS GATES
pod/devops-info-service-69979f8f89-794fn   1/1     Running   0          77s   10.244.0.15   lab09-kind-control-plane   <none>           <none>
pod/devops-info-service-69979f8f89-mj9tb   1/1     Running   0          92s   10.244.0.13   lab09-kind-control-plane   <none>           <none>
pod/devops-info-service-69979f8f89-t2kwf   1/1     Running   0          87s   10.244.0.14   lab09-kind-control-plane   <none>           <none>

NAME                          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service   NodePort    10.96.75.60   <none>        80:30080/TCP   3m41s   app=devops-info-service
service/kubernetes            ClusterIP   10.96.0.1     <none>        443/TCP        5m50s   <none>

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS            IMAGES                                SELECTOR
deployment.apps/devops-info-service   3/3     3            3           4m5s   devops-info-service   funnyfoxd/devops-info-service:lab02   app=devops-info-service

NAME                                             DESIRED   CURRENT   READY   AGE    CONTAINERS            IMAGES                                SELECTOR
replicaset.apps/devops-info-service-68667d5787   0         0         0       2m2s   devops-info-service   funnyfoxd/devops-info-service:lab02   app=devops-info-service,pod-template-hash=68667d5787
replicaset.apps/devops-info-service-69979f8f89   3         3         3       4m5s   devops-info-service   funnyfoxd/devops-info-service:lab02   app=devops-info-service,pod-template-hash=69979f8f89
```

`kubectl describe deployment/devops-info-service` (replicas + strategy):
```text
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
```

Curl outputs proving the app works:
`curl http://192.168.0.3:30080/health`:
```json
{"status":"healthy","timestamp":"2026-03-20T13:27:20.613412+00:00","uptime_seconds":52}
```

`curl http://192.168.0.3:30080/` (preview):
```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-69979f8f89-t2kwf","platform":"Linux","platform_version":"Linux-6.17.0-19-generic-x86_64-with-glibc2.41","architecture":"x86_64","cpu_count":16,"python_version":"3.13.11"},"runtime":{"uptime_seconds":63,"uptime_human":"0 hours, 1 minute","current_time":"2026-03-20T13:27:21.616112+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

Note on NodePort access:
- `localhost:30080` was not reachable in this environment.
- The working approach was to call NodePort via the node `INTERNAL-IP` (example: `192.168.0.3:30080`).

## Operations Performed (Task 4)
### Commands used for deployment
1. Apply Deployment:
```bash
kubectl --context kind-lab09-kind apply -f k8s/deployment.yml
```
2. Wait for rollout:
```bash
kubectl --context kind-lab09-kind rollout status deployment/devops-info-service --timeout=120s
```
3. Apply Service:
```bash
kubectl --context kind-lab09-kind apply -f k8s/service.yml
```

### Scaling (to 5 replicas)
```bash
kubectl --context kind-lab09-kind scale deployment/devops-info-service --replicas=5
kubectl --context kind-lab09-kind rollout status deployment/devops-info-service --timeout=120s
```

`kubectl rollout status` output (condensed):
```text
Waiting for deployment "devops-info-service" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "devops-info-service" rollout to finish: 4 of 5 updated replicas are available...
deployment "devops-info-service" successfully rolled out
```

At that moment, pods were:
```text
devops-info-service-69979f8f89-7g5hf
devops-info-service-69979f8f89-bjc4w
devops-info-service-69979f8f89-g7dqt
devops-info-service-69979f8f89-ggbtx
devops-info-service-69979f8f89-nqgnh
```

### Rolling update (config change)
To trigger a rollout, we changed the Deployment configuration (added `DEBUG=true` temporarily).

We confirmed service availability during the rollout by repeatedly calling:
`GET /health` via `http://192.168.0.3:30080/health`

During the rolling update, health checks returned `200`:
```text
health_check_1: 200
health_check_2: 200
health_check_3: 200
health_check_4: 200
health_check_5: 200
health_check_6: 200
health_check_7: 200
health_check_8: 200
health_check_9: 200
health_check_10: 200
```

`kubectl rollout status` output (condensed):
```text
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

### Rollback
Rollback capability was demonstrated using Kubernetes rollout undo:
```bash
kubectl --context kind-lab09-kind rollout history deployment/devops-info-service
kubectl --context kind-lab09-kind rollout undo deployment/devops-info-service
kubectl --context kind-lab09-kind rollout status deployment/devops-info-service --timeout=180s
```

`kubectl rollout history` output:
```text
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

`kubectl rollout status` output (condensed):
```text
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

After rollback, the service remained healthy (`/health` returned `200`).

## Production Considerations (Task 5)
Health checks:
- Implemented both `readinessProbe` and `livenessProbe` using `/health`.
- Why:
  - readiness prevents sending traffic to Pods that are not ready.
  - liveness ensures the container is restarted if it hangs or becomes unhealthy.

Resource limits rationale:
- Requests help the scheduler place Pods on nodes with sufficient capacity.
- Limits protect cluster stability by preventing a single Pod from consuming excessive CPU/memory.

Improvements for production:
- Add `HorizontalPodAutoscaler` (HPA) based on CPU/memory or custom metrics.
- Add `PodDisruptionBudget` (PDB) to control availability during node maintenance.
- Prefer `Ingress` (with TLS) or `Gateway API` instead of NodePort for real traffic.
- Use `ConfigMap`/`Secret` for configuration and credentials (instead of hardcoding env values).
- Add monitoring/alerting:
  - Prometheus scraping + Grafana dashboards
  - alert rules for readiness/liveness failures and high restart counts

Monitoring and observability strategy:
- Kubernetes-native signals:
  - `kubectl get events`, Pod `RESTARTS`, rollout status
  - readiness/liveness probe failures
- App-level:
  - structured logs, request latency metrics, uptime metrics (if enabled)

## Challenges & Solutions
Challenge: NodePort connectivity to `localhost`
- Attempting to curl `http://127.0.0.1:30080/health` failed.
- Solution:
  - Curling `http://<kind-node-INTERNAL-IP>:30080/health` worked (example `192.168.0.3`), matching the NodePort exposure model in this environment.

Challenge: Demonstrating zero downtime during rollout
- Solution:
  - Kept probes enabled and verified repeated `/health` calls returned `200` while the rollout progressed (`maxUnavailable: 0`, `maxSurge: 1`).

What I learned:
- Rolling updates are governed by Deployment strategy + readiness/liveness.
- Rollback uses stored ReplicaSets and quickly restores previous template/state.

