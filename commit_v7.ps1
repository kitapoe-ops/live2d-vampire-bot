# Commit v7 — fix SyntaxError in recognition.onerror (missing closing quote)
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v7-syntax): close missing quote in onerror hint string (was SyntaxError breaking widget)"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
