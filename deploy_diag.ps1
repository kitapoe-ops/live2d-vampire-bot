# Deploy to Cloudflare Pages project vampire-widget
$ErrorActionPreference = "Stop"
$envPath = "C:\Users\kitap\.openclaw\.cf-pages-vampire-widget.env"
$env = @{}
Get-Content $envPath | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
        $env[$Matches[1].Trim()] = $Matches[2].Trim()
    }
}

$apiToken = $env["CLOUDFLARE_API_TOKEN"]
$accountId = $env["CLOUDFLARE_ACCOUNT_ID"]
$projectName = $env["PAGES_PROJECT_NAME"]
$distDir = "C:\Users\kitap\.openclaw\workspace\live2d-fork\dist-pages"

Write-Output "Deploying to: $projectName (account $accountId)"
Write-Output "Dist dir: $distDir"

# Read git HEAD
$gitHead = (git -C "C:\Users\kitap\.openclaw\workspace\live2d-fork" rev-parse HEAD).Trim()
Write-Output "Git HEAD: $gitHead"

# Use the wrangler-style direct upload via Cloudflare API
$headers = @{
    "Authorization" = "Bearer $apiToken"
    "Content-Type" = "application/json"
}

# First create a deployment
$url = "https://api.cloudflare.com/client/v4/accounts/$accountId/pages/projects/$projectName/deployments"
$body = @{
    # branch + commit metadata
    # we'll upload as direct upload below
} | ConvertTo-Json

# Use direct upload (multipart)
$uri = "https://api.cloudflare.com/client/v4/accounts/$accountId/pages/projects/$projectName/deployments"

$zipPath = "$env:TEMP\pages-deploy-$gitHead.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath }

Add-Type -AssemblyName "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory($distDir, $zipPath)
Write-Output "Created zip: $zipPath ($((Get-Item $zipPath).Length) bytes)"

# Multipart form upload
$form = @{
    "branch" = "main"
    "commit" = $gitHead
    "commit_message" = "fix(mobile-mic-v4-diag): rich diagnostic dump in onerror handler"
    "commit_dir" = "/*"
}

# Use curl since multipart upload with PS is annoying
$deployUrl = $null
$output = & curl.exe -s -X POST `
    -H "Authorization: Bearer $apiToken" `
    -F "branch=main" `
    -F "commit=$gitHead" `
    -F "commit_message=fix(mobile-mic-v4-diag): rich diagnostic dump" `
    -F "file=@${zipPath}" `
    "$uri" 2>&1

$json = $output | ConvertFrom-Json
if ($json.success) {
    $deployUrl = $json.result.url
    $id = $json.result.id
    Write-Output "DEPLOY OK"
    Write-Output "URL: $deployUrl"
    Write-Output "ID:  $id"
} else {
    Write-Error "DEPLOY FAILED: $($json.errors | ConvertTo-Json)"
    exit 1
}

Remove-Item $zipPath -ErrorAction SilentlyContinue
