$procs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*http.server*8001*' }
if ($procs) {
    foreach ($p in $procs) {
        Write-Host "Stopping python.exe PID=$($p.Id)"
        Stop-Process -Id $p.Id -Force
    }
} else {
    Write-Host "No python http.server :8001 process found (already stopped)"
}
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize
