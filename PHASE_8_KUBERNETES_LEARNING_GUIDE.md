# Phase 8 Kubernetes Learning Guide: Local Cluster Deployment

Welcome to the **Phase 8 Learning Guide**. In this phase, we elevate our containerized architecture from a single-host environment (Docker Compose) into a production-style declarative orchestrator using **Kubernetes** locally with **Minikube**.

---

## 1. What is Kubernetes?

**Kubernetes (also known as K8s)** is an open-source container orchestration platform designed to automate the deployment, scaling, management, and recovery of containerized applications. 

Rather than running commands to launch individual processes, K8s lets you write declarative configurations (YAML files) detailing your desired application state (e.g., *"run 3 backend replicas, mount this disk, and load-balance them"*). Kubernetes constantly monitors the cluster, reconciling any drift to ensure the cluster remains in that desired state.

---

## 2. Why Kubernetes is Needed After Docker

While Docker containerizes the application environment, running containers on a single host is a single point of failure.
*   **Docker Compose Limits:** Docker Compose is a developer-focused tool designed for orchestrating containers on a *single physical computer*. It has no native mechanism to schedule containers across multiple hosts, auto-scale them dynamically based on user load, or replace host machines when they crash.
*   **Enterprise Scaling:** In production, you require a system that spans hundreds of cloud instances, manages routing dynamically, handles automatic rollouts, isolates team workspaces (namespaces), and performs auto-healing. This is what Kubernetes does.

---

## 3. What Problems Phase 8 Solves

By implementing Kubernetes, we transition our AI Knowledge Assistant to an enterprise-grade cloud-native configuration:
*   **Declarative Infrastructure:** We define our entire environment, storage claims, routing ingress rules, secrets, and configuration keys in YAML manifests. This is true Infrastructure as Code (IaC).
*   **Decoupled Secret Management:** Sensitive variables like `GEMINI_API_KEY` are isolated into standard Kubernetes Secrets, decoupled from image build contexts and codebases.
*   **Local Multi-container Networking:** Communication between backend agents and MCP servers uses Kubernetes Services, leveraging the cluster's internal DNS resolution.
*   **Self-Healing:** If the `mcp-ticket` pod runs out of memory or crashes, Kubernetes automatically detects the failure and replaces it immediately without human intervention.

---

## 4. Understanding Core Kubernetes Objects

| Object | Purpose | Project Example |
| :--- | :--- | :--- |
| **Pod** | The smallest deployable computing unit. It holds one or more tightly coupled containers sharing network and storage namespaces. | A pod running the FastAPI `backend` container. |
| **Deployment** | A controller that defines the desired state for Pods (number of replicas, update strategies, image versions). | The `backend` Deployment, which manages replicas of the FastAPI image. |
| **Service** | An abstraction that defines a logical set of Pods and a policy to access them (ClusterIP, NodePort, LoadBalancer). | The `employee-db-mcp` Service exposing port `8001` internally. |
| **ConfigMap** | An API object used to store non-confidential key-value data, separating settings from image builds. | `ai-assistant-config` storing model names and MCP service URLs. |
| **Secret** | An API object containing small amounts of sensitive data (passwords, tokens, API keys) encoded in base64. | `ai-assistant-secret` containing the base64 encoded `GEMINI_API_KEY`. |
| **Ingress** | An API object that manages external HTTP/HTTPS access to services, acting as an internal reverse proxy/router. | The Ingress rule mapping `ai-assistant.local/api` to `backend` and `/` to `frontend`. |

---

## 5. What Phase 8 Still Cannot Solve

Because Phase 8 runs on a local cluster (Minikube):
*   **Physical High Availability:** All pods still run on a single host machine (your computer). If your laptop loses power, the cluster dies.
*   **Real Load Balancing:** True cloud load balancers (e.g. AWS ELB, Azure ALB) are not natively available. Minikube maps cluster NodePorts to local IP addresses.
*   **Dynamic DNS:** Exposing services requires editing local `/etc/hosts` configurations.
*   **Cloud Identity Integrations:** Managing permissions using cloud identities (such as AWS IAM or Azure Managed Identities) isn't possible locally.

---

## 6. What Phase 9 (Azure Cloud) Will Solve

In **Phase 9**, we migrate the local Kubernetes configurations to a cloud-managed Kubernetes service like **Azure Kubernetes Service (AKS)**:
*   **Managed Control Plane:** Azure manages master nodes, health checks, and upgrades automatically.
*   **Multi-Node Scaling:** Pods will scale across separate Azure Virtual Machines spanning different Physical Availability Zones.
*   **Cloud Volumes:** Static SQLite/FAISS storages will map to Azure Files or Managed Disks using CSI (Container Storage Interface) drivers.
*   **Cloud Load Balancers:** Kubernetes Services of type `LoadBalancer` will automatically provision Azure Public IP addresses.
*   **Managed Secrets:** Integration with Azure Key Vault to inject secrets dynamically.

---

## 7. 20 Kubernetes Interview Questions and Answers

### Q1: What is the main difference between a Pod and a Container?
*   **Answer:** A container is a single runtime process (e.g., Docker container). A Pod is a Kubernetes abstraction that wraps one or more containers. Containers inside a Pod share the same network namespace (IP and port space), IPC namespace, and storage volumes, allowing them to communicate via localhost.

### Q2: What is the purpose of the Kubernetes Control Plane? List its core components.
*   **Answer:** The Control Plane manages the global state of the cluster, making scheduling decisions, responding to events, and routing traffic. Core components:
    1.  `kube-apiserver`: The gateway exposing the Kubernetes API.
    2.  `etcd`: Consistent, highly-available key-value database for cluster state.
    3.  `kube-scheduler`: Assigns newly created Pods to healthy Nodes.
    4.  `kube-controller-manager`: Runs background controllers (Node, ReplicaSet, Endpoint controllers).

### Q3: What is the difference between `ReplicaSet` and `Deployment`?
*   **Answer:** A `ReplicaSet` ensures that a specified number of pod replicas are running at any given time. A `Deployment` is a higher-level controller that manages ReplicaSets, enabling declarative updates to Pods, rolling updates, rollbacks, and pause/resume deployments.

### Q4: Why should we use `imagePullPolicy: Never` or `IfNotPresent` for local Minikube development?
*   **Answer:** By default, Kubernetes attempts to pull images from public registries (Docker Hub). Using `Never` or `IfNotPresent` forces Kubernetes to check the local Docker daemon context (loaded in Minikube), allowing developers to test local builds without pushing them to external registries.

### Q5: What is the difference between `ClusterIP`, `NodePort`, and `LoadBalancer` Service types?
*   **Answer:** 
    *   `ClusterIP` (Default): Exposes the service on a cluster-internal IP, making it reachable only within the cluster.
    *   `NodePort`: Exposes the service on each Node's IP at a static port (typically `30000-32767`), making it accessible externally.
    *   `LoadBalancer`: Integrates with cloud providers to automatically provision a public load balancer routing traffic to the NodePort.

### Q6: How do Pods resolve service names like `employee-db-mcp` internally?
*   **Answer:** Kubernetes runs a built-in DNS service (`CoreDNS`). When a Service named `employee-db-mcp` is created, CoreDNS registers its name mapping to its internal ClusterIP. Pods lookup this hostname, and traffic is routed automatically.

### Q7: Explain the role of `kube-proxy` on Kubernetes nodes.
*   **Answer:** `kube-proxy` is a network agent running on each Node. It monitors the API server for changes to Service and Endpoint objects and updates local IPVS or iptables routing rules to forward traffic directed at a Service IP to the backing Pods.

### Q8: What is an Ingress Controller? How does it differ from a standard Service?
*   **Answer:** An Ingress Controller is a specialized Pod (often Nginx or Traefik) that acts as a reverse proxy, routing external HTTP/HTTPS traffic to internal Services based on hostnames or URL paths. A Service exposes a single port, whereas Ingress exposes multiple services under a unified hostname/IP.

### Q9: How do you encode Secrets in Kubernetes manifests? Is this secure?
*   **Answer:** Secrets are written in base64 encoding (e.g. `echo -n "key" | base64`). This is **not secure** on its own because base64 is encoding, not encryption. In production, Secrets must be encrypted at rest in `etcd`, protected by RBAC, or dynamically retrieved from vaults like Azure Key Vault or HashiCorp Vault.

### Q10: What is the difference between `PersistentVolume` (PV) and `PersistentVolumeClaim` (PVC)?
*   **Answer:** A `PersistentVolume` is a storage resource provisioned by an administrator or storage class. A `PersistentVolumeClaim` is a request for storage by a user, specifying access modes (RWO, RWX) and size. K8s automatically binds matching PVs to PVCs.

### Q11: Why is `ReadWriteOnce` (RWO) the most common access mode?
*   **Answer:** `ReadWriteOnce` means the volume can be mounted as read-write by a *single node* at a time. This is because standard block storage (like AWS EBS or Azure Disk) cannot be safely mounted by multiple machines concurrently without filesystem corruption.

### Q12: How do you share files between two pods using PVCs locally?
*   **Answer:** In single-node environments (like Minikube), both pods run on the same physical host. Therefore, a PVC using the local storage class can be mounted by both the `backend` and `mcp-document` pods simultaneously, resolving local sharing constraints.

### Q13: Explain how `livenessProbe` and `readinessProbe` differ.
*   **Answer:** 
    *   `livenessProbe`: Determines if a container is running. If it fails, K8s kills and restarts the container.
    *   `readinessProbe`: Determines if a container is ready to accept traffic. If it fails, K8s removes its IP from the backing Service's endpoints so no traffic is routed to it.

### Q14: How does rolling update deployment work in Kubernetes?
*   **Answer:** During a rolling update, the Deployment launches a new Pod using the new image version while keeping the old Pods running. Once the new Pod passes its readiness probe, the controller terminates one old Pod. This continues step-by-step, achieving zero downtime.

### Q15: What is the command to view logs of a container in a Pod containing multiple containers?
*   **Answer:** 
    ```bash
    kubectl logs <pod_name> -c <container_name>
    ```

### Q16: How do you access a NodePort service in Minikube?
*   **Answer:** Use the helper command:
    ```bash
    minikube service <service_name> --url
    ```
    *This creates a proxy tunnel from the Minikube VM to your local machine.*

### Q17: What does `kubectl exec` do? Give an example.
*   **Answer:** It runs a command directly inside a container of a running Pod, similar to `docker exec`. Example:
    ```bash
    kubectl exec -it backend-pod-name -- /bin/bash
    ```

### Q18: What is a headless service, and when is it used?
*   **Answer:** A headless service is defined by setting `spec.clusterIP: None`. It doesn't allocate an internal IP. Instead, DNS lookups return the direct IP addresses of all backing Pods. This is used for stateful applications like database clusters where pods must talk directly.

### Q19: Explain the difference between ConfigMaps and Secrets.
*   **Answer:** ConfigMaps store non-sensitive configuration parameters as plain text. Secrets store sensitive parameters (keys, certificates) and are stored in memory on nodes, obfuscated in base64, and decoupled from standard logs.

### Q20: How do you verify that your Ingress configuration is working locally?
*   **Answer:** 
    1.  Enable the ingress addon: `minikube addons enable ingress`.
    2.  Add host mapping: Add the line `<minikube-ip> ai-assistant.local` to your local `/etc/hosts` file.
    3.  Browse: Open `http://ai-assistant.local/` in your browser.
