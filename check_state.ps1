$ErrorActionPreference = 'Continue'
Write-Host "=== Listening on port 8000 ==="
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Format-List LocalAddress, LocalPort, OwningProcess

Write-Host "`n=== python.exe processes ==="
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, @{n='Cmd';e={ ($_.Path) }} | Format-Table -AutoSize -Wrap

Write-Host "`n=== cloudflared processes ==="
Get-Process cloudflared -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize

Write-Host "`n=== Healthz from local FastAPI ==="
try { Invoke-WebRequest -Uri 'http://127.0.0.1:8000/healthz' -UseBasicParsing -TimeoutSec 3 | Select-Object StatusCode, StatusDescription } catch { Write-Host "Local FastAPI not responding on 8000: $($_.Exception.Message)" }
