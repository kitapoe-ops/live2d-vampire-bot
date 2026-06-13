# Commit v8 — drop frame-ancestors from CSP to fix Android Chrome mic
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v8-csp): drop frame-ancestors from CSP to fix Android Chrome mic double-enforcement conflict"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
