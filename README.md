# Kubernetes Security Lab

[![Kubernetes Security Checks](https://github.com/EmilAlizada/kubernetes-security-lab/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/EmilAlizada/kubernetes-security-lab/actions/workflows/ci.yml)

A hands-on Kubernetes hardening lab that demonstrates how I design workloads around **least privilege, workload isolation, deny-by-default networking, resource governance, and security regression testing**.

> Portfolio / learning project. The manifests are intentionally small enough to audit line by line, while still modeling controls that matter in real Kubernetes environments.

## What this lab demonstrates

- Namespace-level Pod Security Admission labels using the `restricted` profile
- Non-root workload execution
- `RuntimeDefault` seccomp
- Linux capability dropping
- `allowPrivilegeEscalation: false`
- Read-only root filesystems
- Service-account token automount disabled
- No RBAC permissions granted to the application
- Resource requests and limits
- ResourceQuota and LimitRange guardrails
- Liveness and readiness probes
- PodDisruptionBudget
- ClusterIP-only service exposure
- Default-deny ingress and egress
- Explicit client-to-application NetworkPolicy
- Security-focused automated tests in CI

## Security model

```text
                    Kubernetes namespace
             pod-security: restricted / latest
                            |
            +---------------+---------------+
            |                               |
            v                               v
     secure-demo pods                 security-client
     2 replicas                       diagnostic pod
            |                               |
            | <--- explicit policy ---------+
            |
      ClusterIP Service

Default state:
  ingress = DENY
  egress  = DENY

Workload privileges:
  root                  = DENY
  privilege escalation  = DENY
  Linux capabilities    = DROP ALL
  writable root FS      = DENY
  API token mount       = DENY
```

## Repository layout

```text
.
├── .github/
│   ├── dependabot.yml
│   └── workflows/ci.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── LAB_GUIDE.md
│   └── THREAT_MODEL.md
├── k8s/
│   ├── namespace.yaml
│   ├── resource-quota.yaml
│   ├── limit-range.yaml
│   ├── service-account.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── pod-disruption-budget.yaml
│   ├── network-policy-default-deny.yaml
│   ├── network-policy-allow-client.yaml
│   ├── client.yaml
│   └── kustomization.yaml
├── tests/
│   └── test_security_controls.py
├── .yamllint.yml
├── Makefile
├── SECURITY.md
└── requirements-dev.txt
```

## Quick start

Requirements:

- a Kubernetes cluster
- `kubectl` with Kustomize support

Apply the lab:

```bash
kubectl apply -k k8s/
```

Wait for the deployment:

```bash
kubectl -n security-lab rollout status deployment/secure-demo
```

Inspect the workload:

```bash
kubectl -n security-lab get pods,svc,networkpolicy
```

### Test the allowed path

The included `security-client` pod is labeled so the NetworkPolicy permits it to contact the service:

```bash
kubectl -n security-lab exec security-client -- \
  curl -fsS http://secure-demo/
```

Expected response:

```text
secure kubernetes workload
```

### Test isolation

A pod without the approved client label should not be able to connect to the application because namespace networking starts from default deny.

See [docs/LAB_GUIDE.md](docs/LAB_GUIDE.md) for a complete walkthrough.

## Automated security controls

CI runs on every push and pull request:

```text
YAML lint
   |
   v
Manifest parsing
   |
   v
Security policy tests
   |
   +--> Pod Security labels
   +--> non-root execution
   +--> seccomp
   +--> no privilege escalation
   +--> DROP ALL capabilities
   +--> read-only root filesystem
   +--> resource requests / limits
   +--> probes
   +--> no latest image tags
   +--> token automount disabled
   +--> default-deny NetworkPolicy
   +--> ClusterIP-only service
```

The point is not just to *document* the hardening. The tests are designed to fail if important controls are removed later.

Run locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

make check
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m yamllint k8s
pytest -q
```

## Important design choices

### No application RBAC

The demo web workload does not need the Kubernetes API, so it receives **no Role or RoleBinding at all**. The service account also has token automount disabled.

Least privilege sometimes means "grant less." Here it means **grant nothing**.

### Network access is explicit

The namespace begins with a policy that denies all ingress and egress. A second policy permits only pods labeled `access: secure-demo` to reach the application on TCP/8080 and to resolve DNS.

### Read-only runtime

The workload root filesystem is read-only. A small memory-backed `emptyDir` is mounted at `/tmp` for the demo application's temporary content.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Lab guide](docs/LAB_GUIDE.md)
- [Security policy](SECURITY.md)

## Roadmap

- [ ] Add image digest pinning
- [ ] Add SBOM and image provenance verification
- [ ] Add admission-policy examples with Kyverno or Gatekeeper
- [ ] Add dedicated secrets-management lab
- [ ] Add runtime detection examples
- [ ] Add a disposable Kind-based integration test

## Explore the portfolio

- [DevSecOps Pipeline](https://github.com/EmilAlizada/devsecops-pipeline)
- [Secure Django API](https://github.com/EmilAlizada/secure-django-api)
- [Python Security Toolkit](https://github.com/EmilAlizada/python-security-toolkit)

[GitHub profile](https://github.com/EmilAlizada)

## Author

**Emil Alizada**  
Cybersecurity · DevOps · Secure Backend Engineering
