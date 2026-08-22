# GitOps Validation Evidence

**Validation date:** 2026-08-22  
**Scope:** `NT114_manifests/argocd/apps/mlops-stock`  
**Environment:** Windows laptop, Helm 4.1.3, kubectl 1.36.1, Terraform 1.14.9

## Validated locally

The chart now includes a complete default `values.yaml`, while `values-dev.yaml` and `values-prod.yaml` remain explicit ArgoCD overlays. The dev and prod ArgoCD `Application` objects use the canonical public repository:

```text
https://github.com/erotonin/NT114-MLOps-Stock.git
```

The chart path is:

```text
argocd/apps/mlops-stock
```

The following commands completed successfully from the chart directory:

```powershell
helm lint .
helm lint . -f values-dev.yaml
helm template mlops-stock . -n mlops-stock-dev -f values-dev.yaml
```

Both lint runs reported **0 chart failures**. Helm rendered **24 Kubernetes documents** for the dev overlay. The rendered output was parsed offline by `scripts/validate_rendered_yaml.py`; the check passed and confirmed the expected Redis resources, seven application Services, seven Deployments/StatefulSet resources, and one Ingress.

The offline validator is intentionally structural. It checks that every rendered document is a mapping containing `apiVersion`, `kind`, `metadata`, and a non-empty `metadata.name`. It does not claim that the manifests have been accepted by an API server.

## Checks intentionally not claimed

No Kubernetes cluster was available in the laptop context. `kubectl apply --dry-run=client` still attempted API discovery with the installed kubectl client, so no server-side or schema-backed Kubernetes validation is claimed. No `kubectl apply`, ArgoCD sync, EKS deployment, or production rollout was performed.

The manifests repository contains no Terraform `.tf` files in the audited tree. Therefore, Terraform `init`/`validate` was not applicable to this checkout; this is recorded as **not applicable**, not as a successful infrastructure validation.

The image references in the legacy dev/prod overlays still point to the existing `quackusarle/*` container registry namespace. The source repository URL is now canonicalized to `erotonin/NT114-MLOps-Stock`, but registry ownership and image publication are separate concerns. A real cloud deployment must verify that those images remain available or publish equivalent images under a controlled registry before syncing ArgoCD.

## Reproduction

From PowerShell:

```powershell
Set-Location C:\Users\Admin\Desktop\NT114\NT114_manifests\argocd\apps\mlops-stock
helm lint .
helm lint . -f values-dev.yaml
helm template mlops-stock . -n mlops-stock-dev -f values-dev.yaml > ..\..\..\artifacts\mlops-stock-rendered.yaml
python ..\..\..\scripts\validate_rendered_yaml.py ..\..\..\artifacts\mlops-stock-rendered.yaml
```

These checks validate chart rendering and manifest structure only. They do not replace a real-cluster smoke test.
