# AWS Cloud Operations & Incident Response

**AWS operational engineering: networking, identity, observability, automation, incident response and recovery.**

A structured, evidence-driven AWS CloudOps practice repository, drawing on AWS-authored training, official workshops, service documentation and AWS Samples projects.

> **Status: PLANNED.** No production-grade capabilities, live AWS experiments, assessments or incident-response results are claimed to have been completed. This repository is an educational sandbox and is not an AWS product or an official AWS course.

## Mission

Develop verifiable hands-on skills for Cloud Engineer / CloudOps / SRE roles, **without duplicating** the separate [KPCP](https://github.com/miku-wwl/kube-platform-control-plane) Kubernetes/Terraform control-plane project.

This repository focuses on **operating and troubleshooting existing AWS services**, not on creating another infrastructure platform. Prefer a minimal disposable workload and short-lived isolated AWS resources to expansive IaC environments.

## Learning tracks

| Track | Main skills | Official starting points |
|---|---|---|
| A01 — Architecture | AWS Well-Architected, reliability, operational excellence | [Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/) |
| A02 — Networking | VPC, route tables, SG/NACL, endpoints, Reachability Analyzer | [AWS Networking Workshop](https://catalog.workshops.aws/networking/en-US) |
| A03 — Identity | IAM roles, STS, least privilege, IAM Access Analyzer | [IAM Access Analyzer Workshop](https://catalog.workshops.aws/accessanalyzercicd) |
| A04 — Observability | CloudWatch, alarms, Logs Insights QL, CloudTrail | [CloudWatch Logs Insights tutorials](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData_Tutorials.html) |
| A05 — Operations Automation | Systems Manager inventory, State Manager, Run Command, Automation | [AWS Cloud and Hybrid Operations Workshop](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop) |
| A06 — Governance | AWS Config, CloudTrail, inventory, cost controls | [AWS Cloud and Hybrid Operations Workshop](https://github.com/aws-samples/aws-cloud-and-hybrid-operations-workshop) |
| A07 — Recovery | AWS Backup, EBS/EC2 recovery, RTO/RPO | [AWS Backup getting started](https://docs.aws.amazon.com/aws-backup/latest/devguide/getting-started.html) |
| A08 — Incident Response | Diagnostics, containment, recovery, RCA, runbooks | [AWS Incident Response Playbook Samples](https://github.com/aws-samples/aws-incident-response-playbooks) |

For the **Chinese study roadmap**, source classifications, cost guardrails and acceptance criteria, see [`docs/AWS_SPECIALTY_ROADMAP.md`](docs/AWS_SPECIALTY_ROADMAP.md).

## Candidate technical exercises

1. Trace and resolve a VPC connectivity problem with route tables, security groups and Reachability Analyzer.
2. Reproduce an IAM `AccessDenied` event, diagnose it using CloudTrail and validate a least-privilege policy.
3. Produce and query structured application error logs using CloudWatch Logs Insights, and verify one actionable alarm.
4. Write a **read-only by default** Python or shell inventory/diagnostic script and test it against mock fixtures.
5. Examine AWS Config drift/compliance evidence without developing a replacement IaC control plane.
6. Back up an isolated test resource, restore it, and validate data integrity and measured recovery time.
7. Record at least two synthetic-incident RCAs, including root cause, evidence, remediation and prevention.

All live modifications must be explicitly scoped to an isolated account or sandbox and performed manually with verified permissions. No AWS API mutations occur merely by cloning this repository.

## Recommended official practical assessments

- [AWS Application Networking Demonstrated](https://aws.amazon.com/blogs/training-and-certification/march-2026-new-offerings/)
- [AWS Incident Response Demonstrated](https://aws.amazon.com/blogs/training-and-certification/march-2026-new-offerings/)

AWS microcredentials are hands-on assessments. They are distinct from AWS certifications and may have changing access or regional conditions; confirm current details in AWS Skill Builder before registering.

## Repository structure

```text
aws-cloudops/
├── README.md
├── docs/
│   ├── AWS_SPECIALTY_ROADMAP.md
│   ├── JD_SKILL_MAPPING.md
│   ├── STATUS.md
│   ├── templates/
│   │   ├── EXPERIMENT.md
│   │   └── INCIDENT_RCA.md
│   └── incidents/
├── automation/                  # Read-only scripts and tested diagnostics
├── monitoring/logs-insights/    # Saved Logs Insights QL queries
├── security/iam/                # Least-privilege policy analysis, sanitized
├── evidence/                    # Sanitized experiment evidence only
└── tests/                       # Offline/unit checks
```

## Safeguards and claims

- Use an isolated AWS sandbox, least-privilege permissions, and fixed resources/time windows.
- Check actual regional prices before each lab, including NAT Gateway, Network Firewall, Config, CloudWatch Logs, AWS Backup, and Reachability Analyzer.
- **AWS Budgets notifications are not spending hard stops.** Monitor and remove all resources afterward.
- Do not commit AWS keys, session tokens, account IDs, ARNs with sensitive information, private IP inventories, or raw CloudTrail/customer logs.
- Keep `Planned`, `Local Verified`, `AWS Verified`, `Blocked`, and `Not Run` separate in status and resume claims.
- [AWS Systems Manager Incident Manager](https://docs.aws.amazon.com/incident-manager/latest/userguide/incident-manager-availability-change.html) and [Change Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/change-manager-availability-change.html) stopped onboarding new customers in November 2025. Do **not** follow legacy workshop steps that require enabling either service in a new account.

## Attribution

This independent study repository links to content published by AWS Training, AWS documentation, and AWS Samples. The **learning sequence, experiments, gates and project structure are independently curated**, not an official AWS curriculum. External source code is not copied into this starter.

## Status

**Planning / repository initialization — no completed live experiments.**
