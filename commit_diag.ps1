# Commit diagnostic instrumentation
Set-Location "C:\Users\kitap\.openclaw\workspace\live2d-fork"

$status = git status --short
Write-Output "Git status:"
Write-Output $status

git add -A
$msg = "fix(mobile-mic-v4-diag): rich diagnostic dump in onerror handler (console + localStorage)"
Write-Output "Committing: $msg"
git commit -m $msg

Write-Output "Pushing to origin main..."
git push origin main

Write-Output "Done. HEAD:"
git log -1 --oneline
