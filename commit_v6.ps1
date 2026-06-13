# Commit v6 — browser detection for SR support
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v6-browser): detect non-Chrome Android browsers + disable mic button"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
