# Commit v13 — fix no-speech recursive error loop (60s blocking)
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v13-no-recursive): no-speech fallback setTimeout 200ms + abort flag per user #17321"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
