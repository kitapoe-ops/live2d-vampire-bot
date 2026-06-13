# Commit v5 — boot diagnostics + welcome bubble
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v5-boot): boot-success/error diagnostic dump + first-load welcome bubble guarantee"
git commit -m $msg 2>&1 | Select-Object -First 5
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
