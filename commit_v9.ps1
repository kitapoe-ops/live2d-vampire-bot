# Commit v9 — drop security headers per user request
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v9-no-security): drop X-Frame-Options + CSP + Permissions-Policy per user #17185"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
