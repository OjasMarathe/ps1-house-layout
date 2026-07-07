# Deploying the House-Design Pipeline on Kubernetes (EC2 + S3)

This is the runbook for containerising the PS1+PS2 pipeline and running it as a
scalable service on a self-managed Kubernetes cluster on AWS EC2. It maps directly
onto the detailed guide in `kubernetes.md`; this file is the **project-specific**
version with what's already done and exactly what to run.

---

## 0. Decoding the brief

Your sir's notes, line by line:

| His note | What it means |
|---|---|
| "create EC2 instance, that becomes node" | An **EC2 instance is a virtual machine**; once you install Kubernetes on it, it acts as a **node** in the cluster. |
| "install kubernetes / one node → cluster" | Install `kubeadm`+`kubelet`. `kubeadm init` on one EC2 turns it into a one-node **cluster** (control plane). Join more EC2s as **worker nodes**. |
| "within the node (container) → spin up the pod → make image run it" | Inside a node, Kubernetes schedules a **Pod**, which wraps your **Container**, which runs your **Docker image**. |
| "how is it spinning more containers so querying doesn't [bottleneck]" | Under load, the **HPA** spins up **more Pods** (each a copy of the container). The **Service** load-balances queries across them, so no single pod is the bottleneck. |
| "store Docker Image" | Push the image to a registry — **ECR** (AWS) or Docker Hub — so the cluster can pull it. |

**The layered mental model (memorise this — it's the whole picture):**

```
AWS Cloud
  └── EC2 instance (a virtual machine)
        └── Kubernetes Node
              └── Pod
                    └── Container  ← our Docker image runs here
                          └── FastAPI app → Z3 pipeline
   S3  = stores the building-code rule files (our "model artifacts")
   ECR = stores the Docker image
```

---

## 1. What is already DONE (locally, demonstrable today)

✅ **Serving app** (`serve_app.py`) — FastAPI wrapping the real pipeline:
`/health`, `/cities`, `/optimize`, `/verify`, `/generate`.
✅ **Dockerfile** — builds a clean `python:3.11-slim` image (`house-pipeline:v1`).
✅ **Built & ran the container**, tested every endpoint:
- `GET /optimize?city=bellevue` → `2568 sq ft`
- `POST /generate` → exterior + **Z3-verified** 8-room interior, ~40 ms
✅ **Found & fixed a real bug:** Z3 is **not thread-safe** — 10 concurrent requests
segfaulted the pod (`exit 139`, `ASSERTION VIOLATION ast.cpp`). Fixed with a
serialization lock; **60 requests / 12 concurrent → all 200, pod stays up.**
✅ **All 5 Kubernetes manifests** written (`k8s/`).
✅ **S3 artifact pattern** (`artifacts.py`) — pulls city codes from S3 at startup,
or uses the baked-in copies if no bucket is set.

**Run the local demo (one terminal):**
```bash
docker build -t house-pipeline:v1 .
docker run -d --name hp -p 8000:8000 house-pipeline:v1
curl localhost:8000/optimize?city=seattle
curl -X POST localhost:8000/generate -H "Content-Type: application/json" -d '{"city":"seattle","vibe":"Entertainer"}'
```

---

## 2. The scaling story (answers "so querying doesn't bottleneck")

Because **Z3 is single-threaded per pod**, you do **not** scale by adding threads
inside one pod — you scale by adding **pods**:

```
            Service (load-balancer, NodePort :30080)
            ┌───────────┬───────────┬───────────┐
          Pod 1       Pod 2       Pod 3  ...   Pod N        ← HPA adds/removes these
         (1 Z3)      (1 Z3)      (1 Z3)       (1 Z3)
```

- One pod handles one Z3 query at a time (fast — ~40 ms).
- The **HPA** watches CPU; above 70% it adds pods (up to 8).
- The **Service** spreads incoming queries across all pods.
- → throughput scales **horizontally**. This is *the* reason to use Kubernetes here.

---

## 3. Production steps on AWS (the path from here)

### Step 1 — Push the image to a registry (ECR)
```bash
aws ecr create-repository --repository-name house-pipeline
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
docker tag house-pipeline:v1 <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/house-pipeline:v1
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/house-pipeline:v1
```
Then put that image URI into `k8s/deployment.yaml`.

### Step 2 — Launch EC2 + build the cluster
- 1× control-plane EC2 (`t3.medium`), 1+ worker EC2 (`t3.large`), same VPC/subnet.
- Security group inbound: `6443`, `10250`, `30000-32767` (NodePort), `22`.
- On every node: install `containerd` + `kubeadm/kubelet/kubectl`, `swapoff -a`.
- Control plane: `kubeadm init --pod-network-cidr=192.168.0.0/16`, install Calico CNI.
- Workers: run the printed `kubeadm join ...`.
- Verify: `kubectl get nodes` → all `Ready`.
*(Full commands are in `kubernetes.md` §8.)*

### Step 3 — S3 for the building-code artifacts
```bash
aws s3 mb s3://my-house-codes
aws s3 cp citycodes/ s3://my-house-codes/citycodes/ --recursive
```
Attach an IAM role to the **worker nodes** allowing `s3:GetObject`/`s3:ListBucket`
on that bucket (guide §9, Option A). Then set `S3_BUCKET: "my-house-codes"` in
`k8s/configmap.yaml`. (Leave it empty to just use the JSONs baked into the image.)

### Step 4 — Install metrics-server (so the HPA can read CPU)
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Step 5 — Deploy
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl get pods -n house-pipeline -w        # wait for Running + Ready
```

### Step 6 — Test the live endpoint
```bash
curl -X POST http://<worker-public-ip>:30080/generate \
  -H "Content-Type: application/json" -d '{"city":"seattle","vibe":"Balanced"}'
```

### Step 7 — Load-test and watch it autoscale
```bash
# terminal 1: hammer the endpoint
hey -n 2000 -c 100 -m POST -H "Content-Type: application/json" \
  -d '{"city":"seattle","vibe":"Balanced"}' http://<worker-ip>:30080/generate
# terminal 2: watch pods scale up
kubectl get hpa -n house-pipeline -w
kubectl get pods -n house-pipeline -w
```

---

## 4. Updating things without a rebuild

- **New city / changed code values** → upload JSON to S3, roll the pods:
  `kubectl rollout restart deploy/house-pipeline -n house-pipeline`
- **New app code** → rebuild + push image, then
  `kubectl set image deploy/house-pipeline house-pipeline=<ecr>/house-pipeline:v2 -n house-pipeline`

---

## 5. Files in this deliverable

```
serve_app.py            FastAPI service (runs inside the pod)
artifacts.py            S3 pull of city-code artifacts (optional)
Dockerfile              builds house-pipeline:v1
.dockerignore           keeps the image lean
requirements-serve.txt  fastapi, uvicorn, z3-solver, boto3
k8s/namespace.yaml      the namespace
k8s/configmap.yaml      S3 + region config
k8s/deployment.yaml     2 replicas, /health probes, resource limits
k8s/service.yaml        NodePort :30080, load-balances across pods
k8s/hpa.yaml            autoscale 2→8 pods on 70% CPU
DEPLOY.md               this runbook
kubernetes.md           the full generic guide (reference)
```
