# 第 06 讲实验 6-3（PowerShell 版）：扮演角色并读取两个对象；结束后恢复原环境变量。
# 用法：.\Test-A06Access.ps1 -RoleArn <arn> -Bucket <name> [-SessionPolicyFile session.json]
param(
    [Parameter(Mandatory = $true)][string]$RoleArn,
    [Parameter(Mandatory = $true)][string]$Bucket,
    [string]$SessionPolicyFile = ""
)
$env:AWS_PAGER = ""
$saved = @{}
foreach ($n in 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN') { $saved[$n] = [Environment]::GetEnvironmentVariable($n) }

$cliArgs = @('sts', 'assume-role', '--role-arn', $RoleArn, '--role-session-name', "a06-probe-$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())",
          '--duration-seconds', '900', '--output', 'json')
if ($SessionPolicyFile) { $cliArgs += @('--policy', "file://$SessionPolicyFile") }
$resp = aws @cliArgs | ConvertFrom-Json
if (-not $resp) { Write-Host "AssumeRole 失败：检查信任策略、操作者权限与 SCP"; exit 1 }

try {
    $env:AWS_ACCESS_KEY_ID = $resp.Credentials.AccessKeyId
    $env:AWS_SECRET_ACCESS_KEY = $resp.Credentials.SecretAccessKey
    $env:AWS_SESSION_TOKEN = $resp.Credentials.SessionToken
    Write-Host "== 当前身份（应为 assumed-role 会话）"
    aws sts get-caller-identity --query Arn --output text
    foreach ($key in 'logs/health.txt', 'reports/summary.csv') {
        $tmp = New-TemporaryFile
        aws s3api get-object --bucket $Bucket --key $key $tmp.FullName 2>$null | Out-Null
        $code = $LASTEXITCODE
        Remove-Item $tmp -Force
        if ($code -eq 0) { Write-Host "✓ $key  exit=0" } else { Write-Host "✗ $key  exit=$code（AccessDenied 或其他错误）" }
    }
}
finally {
    foreach ($n in $saved.Keys) { [Environment]::SetEnvironmentVariable($n, $saved[$n]) }
}
