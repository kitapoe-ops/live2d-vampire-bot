# Commit v11 — remove hard browser block + per-browser diagnostic
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v11-no-hard-block): let Brave/Edge/Firefox try SR; per-browser not-allowed hint per user #17226"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
