#!/usr/bin/env bash
# 第 13 讲实验 13-4 ⓪：只读预检——区域设置、现有备份库 / 计划 / 受保护资源。
set -uo pipefail
REGION="${1:-us-east-1}"; export AWS_PAGER="" PYTHONIOENCODING=utf-8
aws backup describe-region-settings --region "$REGION" --output json | python -c "
import json,sys
d=json.load(sys.stdin)
print('DynamoDB 已纳入 AWS Backup：', d['ResourceTypeOptInPreference'].get('DynamoDB'))
print('DynamoDB 高级功能（由 AWS Backup 完整管理）：', d.get('ResourceTypeManagementPreference',{}).get('DynamoDB'))
print('已纳入的资源类型：', sum(1 for v in d['ResourceTypeOptInPreference'].values() if v), '/', len(d['ResourceTypeOptInPreference']))"
echo "备份库：$(aws backup list-backup-vaults --region "$REGION" --query 'length(BackupVaultList)' --output text)  计划：$(aws backup list-backup-plans --region "$REGION" --query 'length(BackupPlansList)' --output text)  受保护资源：$(aws backup list-protected-resources --region "$REGION" --query 'length(Results)' --output text)  恢复测试计划：$(aws backup list-restore-testing-plans --region "$REGION" --query 'length(RestoreTestingPlans)' --output text)"
echo "DynamoDB 表：$(aws dynamodb list-tables --region "$REGION" --query 'length(TableNames)' --output text)"
