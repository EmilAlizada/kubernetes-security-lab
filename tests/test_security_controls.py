from pathlib import Path

import yaml

K8S_DIR = Path(__file__).resolve().parents[1] / "k8s"


def load_manifests():
    manifests = []
    for path in sorted(K8S_DIR.glob("*.yaml")):
        if path.name == "kustomization.yaml":
            continue
        with path.open(encoding="utf-8") as handle:
            for document in yaml.safe_load_all(handle):
                if document:
                    manifests.append(document)
    return manifests


MANIFESTS = load_manifests()


def find(kind, name):
    for manifest in MANIFESTS:
        if manifest.get("kind") == kind and manifest.get("metadata", {}).get("name") == name:
            return manifest
    raise AssertionError(f"Missing {kind}/{name}")


def pod_specs():
    specs = []
    for manifest in MANIFESTS:
        kind = manifest.get("kind")
        if kind == "Deployment":
            specs.append((f"Deployment/{manifest['metadata']['name']}", manifest["spec"]["template"]["spec"]))
        elif kind == "Pod":
            specs.append((f"Pod/{manifest['metadata']['name']}", manifest["spec"]))
    return specs


def test_namespace_enforces_restricted_pod_security():
    namespace = find("Namespace", "security-lab")
    labels = namespace["metadata"]["labels"]

    assert labels["pod-security.kubernetes.io/enforce"] == "restricted"
    assert labels["pod-security.kubernetes.io/audit"] == "restricted"
    assert labels["pod-security.kubernetes.io/warn"] == "restricted"
    assert labels["pod-security.kubernetes.io/enforce-version"] == "latest"


def test_service_account_token_automount_is_disabled():
    service_account = find("ServiceAccount", "secure-demo")
    assert service_account["automountServiceAccountToken"] is False

    for name, spec in pod_specs():
        assert spec.get("automountServiceAccountToken") is False, name


def test_pods_use_restricted_security_context():
    for name, spec in pod_specs():
        security = spec["securityContext"]

        assert security["runAsNonRoot"] is True, name
        assert security["runAsUser"] != 0, name
        assert security["runAsGroup"] != 0, name
        assert security["seccompProfile"]["type"] == "RuntimeDefault", name

        assert spec.get("hostNetwork", False) is False, name
        assert spec.get("hostPID", False) is False, name
        assert spec.get("hostIPC", False) is False, name


def test_containers_drop_privileges_and_have_resources():
    for workload_name, spec in pod_specs():
        for container in spec["containers"]:
            name = f"{workload_name}:{container['name']}"
            security = container["securityContext"]

            assert security["allowPrivilegeEscalation"] is False, name
            assert security["readOnlyRootFilesystem"] is True, name
            assert security["capabilities"]["drop"] == ["ALL"], name
            assert security.get("privileged", False) is False, name

            resources = container["resources"]
            assert resources["requests"]["cpu"], name
            assert resources["requests"]["memory"], name
            assert resources["limits"]["cpu"], name
            assert resources["limits"]["memory"], name

            image = container["image"]
            assert ":" in image, name
            assert not image.endswith(":latest"), name


def test_deployment_has_health_probes_and_multiple_replicas():
    deployment = find("Deployment", "secure-demo")
    assert deployment["spec"]["replicas"] >= 2

    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert "readinessProbe" in container
    assert "livenessProbe" in container


def test_no_hostpath_volumes_are_used():
    for name, spec in pod_specs():
        for volume in spec.get("volumes", []):
            assert "hostPath" not in volume, name


def test_default_deny_network_policy_exists():
    policy = find("NetworkPolicy", "default-deny-all")
    spec = policy["spec"]

    assert spec["podSelector"] == {}
    assert set(spec["policyTypes"]) == {"Ingress", "Egress"}
    assert "ingress" not in spec
    assert "egress" not in spec


def test_application_ingress_is_explicitly_limited():
    policy = find("NetworkPolicy", "allow-approved-client")
    ingress = policy["spec"]["ingress"]

    assert ingress[0]["from"][0]["podSelector"]["matchLabels"]["access"] == "secure-demo"
    assert ingress[0]["ports"][0]["port"] == 8080


def test_service_is_internal_only():
    service = find("Service", "secure-demo")
    assert service["spec"]["type"] == "ClusterIP"


def test_resource_governance_is_present():
    find("ResourceQuota", "security-lab-quota")
    find("LimitRange", "security-lab-defaults")
    pdb = find("PodDisruptionBudget", "secure-demo")
    assert pdb["spec"]["minAvailable"] == 1


def test_no_rbac_grants_exist():
    forbidden = {"Role", "RoleBinding", "ClusterRole", "ClusterRoleBinding"}
    found = {manifest.get("kind") for manifest in MANIFESTS} & forbidden
    assert not found, f"Unexpected RBAC grants: {sorted(found)}"
