# Commit v12 — fix recognition.lang zh-TW → zh-HK + lang fallback chain
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v12-lang): recognition.lang zh-TW→zh-HK + fallback chain zh-CN/en-US per user #17287"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
