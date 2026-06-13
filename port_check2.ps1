Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 8000 -and $_.LocalPort -lt 8100 } | Format-Table LocalAddress, LocalPort, State, OwningProcess -AutoSize
Write-Host "---"
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 8000 } | Format-Table *
Write-Host "---"
# Try via netstat for cross-check
$netstat = netstat -ano | Select-String ':8000\s'
if ($netstat) {
    Write-Host "netstat -ano port 8000 results:" -ForegroundColor Cyan
    $netstat | ForEach-Object { Write-Host $_.Line }
} else {
    Write-Host "netstat shows NO entries for port 8000" -ForegroundColor Yellow
}
