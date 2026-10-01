# Lab Guide

## 1. Create the lab

```bash
kubectl apply -k k8s/
```

Verify resources:

```bash
kubectl -n security-lab get all
kubectl -n security-lab get networkpolicy
kubectl -n security-lab get resourcequota,limitrange,pdb
```

## 2. Verify Pod Security configuration

```bash
kubectl get namespace security-lab --show-labels
```

The namespace should show the `restricted` profile for enforce, audit, and warn.

## 3. Inspect runtime hardening

```bash
kubectl -n security-lab get deployment secure-demo -o yaml
```

Look for:

- `runAsNonRoot: true`
- non-zero UID/GID
- `seccompProfile.type: RuntimeDefault`
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- `capabilities.drop: [ALL]`
- CPU and memory requests/limits
- disabled service-account token automount

## 4. Test the allowed network path

```bash
kubectl -n security-lab exec security-client -- \
  curl -fsS http://secure-demo/
```

Expected:

```text
secure kubernetes workload
```

## 5. Inspect service-account credentials

The application does not require Kubernetes API access.

```bash
kubectl -n security-lab exec deploy/secure-demo -- \
  sh -c 'test ! -e /var/run/secrets/kubernetes.io/serviceaccount/token && echo token-not-mounted'
```

Expected:

```text
token-not-mounted
```

## 6. Review network isolation

```bash
kubectl -n security-lab describe networkpolicy default-deny-all
kubectl -n security-lab describe networkpolicy allow-approved-client
kubectl -n security-lab describe networkpolicy approved-client-egress
```

The namespace-wide policy establishes deny-by-default behavior. The allow policies then add only the required client traffic.

## 7. Run repository policy tests

```bash
pip install -r requirements-dev.txt
make check
```

Try changing one control locally—for example, set `allowPrivilegeEscalation: true`—and rerun the tests. The policy suite should fail.

That failure is intentional: the tests turn security assumptions into enforceable repository behavior.

## Cleanup

```bash
kubectl delete namespace security-lab
```
