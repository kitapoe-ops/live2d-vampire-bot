$ErrorActionPreference = 'Stop'
# Per MEMORY.md 6-08 incident: NEVER write CLOUDFLARE_API_TOKEN to disk.
# Use GetEnvironmentVariable to read in-memory and pass via env to wrangler process.
$token = [Environment]::GetEnvironmentVariable('CLOUDFLARE_API_TOKEN', 'User')
$accountId = [Environment]::GetEnvironmentVariable('CLOUDFLARE_ACCOUNT_ID', 'User')
if (-not $token) { throw "CLOUDFLARE_API_TOKEN not set in user env. Run: setx CLOUDFLARE_API_TOKEN <token>" }
if (-not $accountId) { throw "CLOUDFLARE_ACCOUNT_ID not set in user env." }

Write-Host "=== Deploying dist-pages/ to Cloudflare Pages project 'vampire-widget' ===" -ForegroundColor Cyan
Write-Host "Account ID: $($accountId.Substring(0, 8))..."
Write-Host "Token: $($token.Substring(0, 12))..." 
Write-Host "Source: C:\Users\kitap\.openclaw\workspace\live2d-fork\dist-pages\"
Write-Host ""

Set-Location 'C:\Users\kitap\.openclaw\workspace\live2d-fork'

# Run wrangler with env vars in-process (per 6-08 protocol, no PS-escaped token)
$env:CLOUDFLARE_API_TOKEN = $token
$env:CLOUDFLARE_ACCOUNT_ID = $accountId

# Use --commit-dirty=true since dist-pages/ is gitignored
# 2026-06-13 v14: use --config wrangler.toml to apply web_analytics = false
wrangler pages deploy dist-pages --project-name vampire-widget --config wrangler.toml --commit-dirty=true --commit-message "fix(mobile-mic): iframe allow speech-recognition + iOS/Android fallback hints" 2>&1

Write-Host ""
Write-Host "=== Deploy complete ===" -ForegroundColor Green
