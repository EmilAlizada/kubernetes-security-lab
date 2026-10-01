# Architecture

## Goal

This lab demonstrates a Kubernetes workload that starts from restrictive defaults and adds only the access required for the demo to function.

## Components

```text
Namespace: security-lab
|
+-- ResourceQuota
+-- LimitRange
+-- ServiceAccount: secure-demo
|   +-- token automount disabled
|   +-- no RBAC bindings
|
+-- Deployment: secure-demo
|   +-- 2 replicas
|   +-- non-root UID/GID
|   +-- RuntimeDefault seccomp
|   +-- DROP ALL capabilities
|   +-- read-only root filesystem
|   +-- resource requests and limits
|   +-- readiness / liveness probes
|
+-- Service: secure-demo
|   +-- ClusterIP only
|
+-- PodDisruptionBudget
|
+-- NetworkPolicy: default-deny-all
+-- NetworkPolicy: allow-approved-client
|
+-- Pod: security-client
    +-- hardened diagnostic client
```

## Identity and API access

The application uses a dedicated ServiceAccount, but there are no RoleBindings or ClusterRoleBindings.

The pod specification and ServiceAccount both set:

```yaml
automountServiceAccountToken: false
```

Because the workload does not need the Kubernetes API, the safest token is no token.

## Filesystem model

The container root filesystem is read-only.

A memory-backed `emptyDir` volume is mounted at `/tmp` to provide a narrowly scoped writable area for temporary application data.

## Network model

The namespace starts with a policy selecting every pod and allowing no ingress or egress.

Explicit policies then allow:

- the labeled diagnostic client to connect to the application on TCP/8080
- the diagnostic client to use cluster DNS

The application itself has no required outbound network access.

## Availability model

The deployment uses two replicas and a PodDisruptionBudget with `minAvailable: 1`.

Readiness and liveness probes are configured independently.

## Resource model

The namespace includes:

- ResourceQuota to bound aggregate consumption
- LimitRange to provide namespace defaults
- explicit requests and limits on each container

These controls reduce the risk of accidental resource starvation and noisy-neighbor behavior.
