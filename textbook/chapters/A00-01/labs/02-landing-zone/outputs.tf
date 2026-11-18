output "landing_zone_arn" {
  description = "Landing Zone ARN，供验收脚本与 get-landing-zone 使用。"
  value       = aws_controltower_landing_zone.this.arn
}

output "drift_status" {
  description = "Landing Zone 漂移状态摘要（IN_SYNC / DRIFTED）。"
  value       = aws_controltower_landing_zone.this.drift_status
}

output "latest_available_version" {
  description = "可升级到的最新 Landing Zone 版本。"
  value       = aws_controltower_landing_zone.this.latest_available_version
}

output "manifest_preview" {
  description = "提交给 Control Tower 的 manifest（便于代码评审）。"
  value       = local.manifest
}
