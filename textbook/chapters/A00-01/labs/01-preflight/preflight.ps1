# A00-01 实验 1（PowerShell 版）：只读预检，不创建、不修改任何资源。
# 用法：pwsh ./preflight.ps1 -HomeRegion us-east-1
param([string]$HomeRegion = "us-east-1")
$env:AWS_PAGER = ""

Write-Host "`n== 1. 当前身份"
$me = aws sts get-caller-identity --output json | ConvertFrom-Json
if (-not $me) { exit 1 }
"{0}  {1}" -f $me.Account, $me.Arn

Write-Host "`n== 2. 组织状态"
$orgRaw = aws organizations describe-organization --output json 2>&1 | Out-String
if ($LASTEXITCODE -eq 0) {
    $org = ($orgRaw | ConvertFrom-Json).Organization
    "Id={0} FeatureSet={1} Management={2}" -f $org.Id, $org.FeatureSet, $org.MasterAccountId
    if ($org.MasterAccountId -eq $me.Account) { "→ 本账户是管理账户。" } else { "→ 本账户是成员账户：Control Tower 只能在管理账户中设置。" }
} elseif ($orgRaw -match "AWSOrganizationsNotInUseException") {
    "→ 不属于任何组织：控制台向导第 2 步会新建组织，本账户将成为管理账户（之后不能更换）。"
} elseif ($orgRaw -match "AccessDenied") {
    "→ 无权限：AccessDenied 不等于组织不存在。"
} else { $orgRaw }

Write-Host "`n== 3. Landing Zone（Home Region = $HomeRegion）"
$lz = (aws controltower list-landing-zones --region $HomeRegion --output json | ConvertFrom-Json).landingZones
if (-not $lz) { "→ 该区域没有 Landing Zone。" }
else {
    $arn = $lz[0].arn
    "→ 已有 Landing Zone：$arn"
    aws controltower get-landing-zone --region $HomeRegion --landing-zone-identifier $arn `
        --query 'landingZone.{version:version,status:status,drift:driftStatus.status,latest:latestAvailableVersion}' --output table
}

Write-Host "`n== 4. 可用基线"
aws controltower list-baselines --region $HomeRegion --query 'baselines[].[name,arn]' --output table

Write-Host "`n== 5. Control Catalog：按行为统计"
(aws controlcatalog list-controls --region $HomeRegion --output json | ConvertFrom-Json).Controls |
    Group-Object Behavior | Select-Object Name, Count | Format-Table -AutoSize
