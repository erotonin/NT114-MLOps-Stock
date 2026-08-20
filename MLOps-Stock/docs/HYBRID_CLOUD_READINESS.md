# Hybrid Cloud Readiness Report

## Scope

The project has a deployment design for a hybrid topology: K3s/on-premise is the training and sensitive-data side; MLflow/PostgreSQL/MinIO provide internal tracking and artifact storage; AWS/EKS is the serving and scaling side; Tailscale or an equivalent private network connects the environments. The related manifests are maintained in the sibling `NT114_manifests` repository.

## What is implemented in manifests

| Capability | Manifest/design evidence | Current acceptance status |
|---|---|---|
| K3s bootstrap | `NT114_manifests/DEPLOYMENT.md` documents K3s and ArgoCD installation | Design/runbook; no cluster execution log in this acceptance |
| MLflow backend | PostgreSQL backend and S3-compatible artifact store are documented | Production design; local Docker uses SQLite/offline profile |
| Object storage bridge | MinIO/SeaweedFS local artifact flow and AWS S3 sync are documented | Cloud-ready design; requires credentials and actual cluster |
| EKS serving | Helm values and IRSA instructions are documented | Manifest readiness; no EKS runtime evidence in this laptop acceptance |
| Secrets | Deployment guide uses Kubernetes Secret/secret-manager placeholders, not committed credentials | Safe by design; operator must provision real secrets |
| GitOps | ArgoCD application templates and environment separation exist | Repository/config evidence |
| Network | Tailscale/private-network component is documented | Requires operator-provided nodes and ACLs |

## Correct defense claim

The project is **Hybrid-Cloud-ready at architecture and deployment-manifest level**, and the local Docker stack is the executable acceptance environment. It is not accurate to say that a production K3s-to-EKS deployment has been proven in this session unless the operator can show cluster logs, `kubectl` output, ArgoCD sync status, MLflow/PostgreSQL/MinIO health and an EKS serving request.

This distinction is a strength rather than a weakness: the thesis separates **implementation evidence** from **deployment design**. The local stack proves the model lifecycle and control-plane behavior; the manifests show how the same lifecycle is promoted to Kubernetes and cloud serving.

## Production checklist

Before calling the Hybrid Cloud deployment production-ready, an operator must provision a K3s cluster, PostgreSQL/MLflow, S3-compatible storage, Tailscale ACLs, cloud IAM/IRSA, TLS ingress, secret manager integration, backup policy, image registry, ArgoCD applications and an EKS cluster. The operator must then record a deployment acceptance run with service health, artifact synchronization, model promotion and an EKS prediction request.

## Defense answer

> “Trong phạm vi nghiệm thu laptop, em chứng minh end-to-end lifecycle bằng Docker Compose local-offline. Phần Hybrid Cloud được thể hiện bằng K3s/EKS Helm/GitOps manifests, MinIO/S3 synchronization design, IRSA và secret-management runbook. Em không gọi đó là production deployment nếu chưa có cluster evidence; đây là deployment-ready architecture và hướng mở rộng trực tiếp.”
