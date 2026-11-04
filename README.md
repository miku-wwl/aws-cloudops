# AWS Cloud Operations & Enterprise Infrastructure

> **Repository:** `miku-wwl/aws-cloudops`  
> **Status:** `PLANNED / NOT LIVE VERIFIED` (documentation and learning plan only)  
> **Focus:** AWS Landing Zones · Organizations & Control Tower · IAM & Governance · Terraform · Enterprise Networking · Observability · Incident Response · Disaster Recovery

## Mission

This repository is an **evidence-driven AWS enterprise infrastructure and CloudOps learning plan**, not a new cloud platform product. It translates the competencies expected of an **AWS Senior Cloud Infrastructure Engineer / Architect** into small, auditable experiments and architecture decisions.

The reference job is [SG Consulting Limited — AWS Senior Cloud Infrastructure Engineer (Auckland)](https://nz.linkedin.com/jobs/view/aws-senior-cloud-infrastructure-engineer-at-sg-consulting-limited-4461019538). Its 10+ years of experience and enterprise production-ownership requirements are **career benchmarks, not experience this repository claims to provide**. A job listing is not a certification syllabus; this learning plan is independently curated.

**Core workflow:** design & trade-offs → authorization/cost check → baseline → controlled change or failure → diagnosis → rollback/recovery → evidence & RCA → teardown.

## Positioning and boundaries

| Project | Primary ownership |
|---|---|
| [KPCP](https://github.com/miku-wwl/kube-platform-control-plane) | Kubernetes control-plane engineering, reconciliation, infrastructure lifecycle and platform automation |
| **AWS CloudOps (this repository)** | AWS multi-account governance, identity/network troubleshooting, infrastructure delivery standards, audit, incident response and recovery |
| [Azure CloudOps](https://github.com/miku-wwl/azure-cloudops) | Azure-specific Landing Zones, networking, governance, Monitor/KQL and incident recovery |

**Non-goals:** another Terraform control plane; Kubernetes management UI; multi-tenant self-service portal; a continuously running enterprise landing zone; and claims of real production on-call or enterprise implementation not backed by work experience. EKS remains an optional integration topic, not the centre of this lab.

## JD-to-learning mapping

| Priority | Enterprise capability | AWS topics | Evidence to produce |
|---|---|---|---|
| **P0** | Multi-account Landing Zone | Organizations, OUs, Control Tower, Account Factory, security/logging accounts, account lifecycle | Architecture diagram, account/OU matrix, two ADRs, lifecycle runbook (design-first) |
| **P0** | Preventive/detective governance | SCP, RCP concepts, Config, Control Tower controls, least privilege, centralized CloudTrail | Policy allow/deny reasoning and test evidence; logging/governance design |
| **P0** | Controlled infrastructure delivery | Terraform module design, pinned versions, remote state, OIDC, CI checks, plan review, drift response | Minimal IaC lab and documented review/rollback/teardown evidence |
| **P0** | Networking and diagnostics | VPC, DNS, routing, SG/NACL, endpoints, PrivateLink, Reachability Analyzer | One independently diagnosed and recovered network fault |
| **P1** | Enterprise connectivity | Transit Gateway, Route 53 Resolver, VPN, Direct Connect, centralized egress/inspection | HLD/ADR and diagnostic decision tree; **live deployment optional** |
| **P1** | Operations, audit and incident response | CloudWatch, Logs Insights QL, CloudTrail, Systems Manager, EventBridge, runbooks | Five queries, actionable alarm, incident timelines and two RCAs |
| **P1** | Resilience and DR | Multi-AZ/Region decisions, AWS Backup, restore, RTO/RPO | Real small-scope restore with integrity check and measured time |
| **P1** | FinOps and operational ownership | tagging, cost allocation, Budgets, cost anomaly analysis, teardown inventory | Cost model and post-exercise resource/cost review |
| **P2** | Advanced enterprise tooling | AFT, Landing Zone Accelerator (LZA), CfCT, Security Hub, GuardDuty, Inspector, WAF/Shield, EKS | Compare/document rather than deploy every service |

See the full [AWS Specialty Roadmap](AWS_SPECIALTY_ROADMAP.md) for modules A00–A10, four sprints, learning resources, cost constraints and acceptance gates.

## Enterprise architecture: design, don't over-deploy

The **reference design** separates a management account, Security OU (e.g. log archive and security tooling), Infrastructure OU (shared networking), Workloads OU (prod/non-prod), and Sandbox OU. These are **architecture examples**, not accounts that have been created in this repository.

- **Organizations** structures accounts and OUs. **IAM Identity Center / IAM** provide identity and access. **SCPs** set permission ceilings for member-account principals; they do **not** grant IAM permissions and do not constrain management-account principals.
- **AWS Control Tower** helps establish/govern a landing zone. Its preventive, detective and proactive controls have different enforcement paths (SCP/RCP, Config, CloudFormation hooks, depending on the control).
- **Account Factory** provisions standardized accounts; **Account Factory for Terraform (AFT)** automates account requests/customizations through Terraform workflows. These are not interchangeable with a simple workload Terraform module.
- **Landing Zone Accelerator (LZA)** extends complex, often regulated landing-zone requirements; it is **not mandatory** for an individual learning lab. AWS's published sample deployment estimate is roughly US$430/month in its specified example environment; actual costs vary.
- An **architecture simulation, single-account lab, Organizations experiment, and full Control Tower deployment are different evidence levels**. Do not claim a multi-account live rollout from a diagram or a single-account `terraform plan`.

## Minimum portfolio outcomes (targets, not achievements)

1. **Enterprise foundation:** a multi-account/OU reference architecture, account lifecycle diagram, permission/guardrail matrix and two architecture decision records.
2. **IaC delivery:** a minimal, disposable Terraform-managed AWS network or workload lab with reviewed `fmt`, `validate`, `plan`; record whether `apply`/`destroy` were actually executed. Describe state security and approval boundaries.
3. **Governance:** explain an SCP-versus-IAM deny and validate the available test path without placing restrictive policies on root or shared organizational OUs.
4. **Networking:** reproduce, diagnose and reverse one isolated SG/route/DNS/endpoints connectivity incident; include exact before/after probes.
5. **Observability and audit:** five executable CloudWatch Logs Insights QL queries; one alarm trigger; a CloudTrail management-event audit timeline with source limitations documented.
6. **Automation:** one read-only-by-default AWS CLI/Python inventory tool with offline tests and a sanitized AWS run when authorized.
7. **Recovery and incident practice:** two distinct synthetic incident RCAs, plus one actual backup **and restore** verification (checksum or equivalent), with RTO/RPO stated correctly.
8. **Economics/security:** up-front cost estimate, scoped permissions, credential-safe evidence and post-cleanup resource/billing review.

## Repository status and evidence rules

**The repository currently contains documentation only** (`README.md`, `AWS_SPECIALTY_ROADMAP.md`, and `LICENSE`). Folders, scripts, automation, deployment files, tests, Terraform state and live evidence described in future tasks **do not yet exist**.

Use evidence states consistently: `PLANNED`, `DESIGNED`, `OFFLINE_PASS`, `STATIC_CHECK_PASS`, `AWS_DEPLOYED`, `AWS_VERIFIED`, `RECOVERED`, `CLEANED_UP`, `BLOCKED`, `NOT_RUN`. Do not equate one state with another. A `terraform validate` pass does not prove successful AWS deployment, and LocalStack or another emulator cannot substitute for verified AWS behavior.

**Safety:** run fault injection only in expressly authorized isolated accounts; avoid permanent access keys; prefer temporary credentials and least privilege; redact account IDs, principals, resource ARNs, private DNS/IPs and raw customer logs. Budget alerts are not hard spending caps. Review leftover EBS snapshots, AWS Backup recovery points, S3 data, log retention, Config recorders, NAT gateways and cross-account resources.

**Legacy AWS caveat:** Systems Manager Incident Manager and Change Manager stopped onboarding new customers in November 2025. Do not treat older workshop steps for those services as a required lab dependency. Use supported CloudWatch/EventBridge/SSM Automation and a documented human approval/response process where appropriate.

## Learning references

- **Detailed plan:** [AWS_SPECIALTY_ROADMAP.md](AWS_SPECIALTY_ROADMAP.md)
- **Job benchmark:** [SG Consulting AWS Senior Cloud Infrastructure Engineer](https://nz.linkedin.com/jobs/view/aws-senior-cloud-infrastructure-engineer-at-sg-consulting-limited-4461019538)
- **Multi-account guidance:** [AWS — Organizing Your AWS Environment](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html)
- **AWS Control Tower:** [User Guide](https://docs.aws.amazon.com/controltower/latest/userguide/) · [Control types](https://docs.aws.amazon.com/controltower/latest/userguide/how-controls-work.html)
- **AFT:** [Account Factory for Terraform](https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html)
- **SCPs:** [AWS Organizations SCP guidance](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)
- **AWS Networking Workshop:** [Workshop Studio](https://catalog.workshops.aws/networking/en-US)
- **AWS Operations:** [Cloud and Hybrid Operations workshop](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop)
- **Incident response:** [AWS incident-response playbook samples](https://github.com/aws-samples/aws-incident-response-playbooks)

This independent learning repository references AWS-authored documentation and samples; it is not an AWS official course or a claim of professional enterprise operations experience.
