# Commit v10 — disable WEBLLM (1GB background download)
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"
git add -A
$msg = "fix(widget-v10-no-webllm): disable WEBLLM (1GB Qwen2.5-1.5B) background download per user #17204"
git commit -m $msg 2>&1 | Select-Object -First 3
git push origin main 2>&1 | Select-Object -First 3
git log -1 --oneline
