# Threat Model

## Scope

This model covers the demo Kubernetes namespace and workload manifests.

It does not claim to model control-plane security, managed-cloud IAM, container-registry security, or a complete production platform.

## Assets

- workload integrity
- namespace availability
- service-to-service network isolation
- cluster API credentials
- node and host isolation
- application availability

## Trust boundaries

1. container process -> container runtime
2. pod -> Kubernetes API
3. pod -> pod network
4. namespace workload -> cluster services
5. manifest repository -> CI validation

## Representative threats and controls

| Threat | Example | Control |
|---|---|---|
| Container privilege escalation | compromised process attempts elevated privileges | non-root, no privilege escalation, DROP ALL |
| Dangerous syscalls | exploit depends on unrestricted syscall profile | RuntimeDefault seccomp |
| Host filesystem access | pod mounts node path | no hostPath volumes |
| Service-account theft | app reads mounted Kubernetes token | token automount disabled |
| Excessive API permissions | compromised app lists cluster resources | no Role/RoleBinding grants |
| Lateral movement | compromised pod scans neighboring services | default-deny NetworkPolicy |
| Unapproved inbound traffic | arbitrary pod reaches application | explicit ingress selector |
| Resource exhaustion | workload consumes namespace capacity | requests, limits, ResourceQuota |
| Disruption during maintenance | all replicas evicted together | two replicas + PDB |
| Writable container tampering | attacker modifies runtime filesystem | read-only root filesystem |
| Unsafe manifest regression | hardening removed in later commit | CI policy tests |

## Residual risks

- container images are tag-pinned but not digest-pinned
- NetworkPolicy enforcement depends on a compatible CNI
- `RuntimeDefault` behavior depends on the container runtime
- secrets management is outside this lab
- admission policy is represented by namespace Pod Security labels, not a custom policy engine
- node, control-plane, and cloud-provider hardening are outside scope

## Next controls

1. pin workload images by digest
2. verify image signatures and provenance
3. add SBOM generation
4. add Kyverno or Gatekeeper policies
5. add a dedicated secrets-management example
6. add runtime security telemetry
