$port = 8000
$conn = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "PORT $port IS listening:" -ForegroundColor Green
    $conn | Format-Table LocalAddress, LocalPort, State, OwningProcess -AutoSize
} else {
    Write-Host "PORT $port is NOT listening locally." -ForegroundColor Yellow
    # Show any non-listen connection on port 8000
    Get-NetTCPConnection | Where-Object { $_.LocalPort -eq $port -or $_.RemotePort -eq $port } | Format-Table LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess -AutoSize
}
Write-Host ""
Write-Host "All listening ports on this host (sample):"
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalAddress -like '127.*' -or $_.LocalAddress -like '0.0.0.0' } | Select-Object -First 20 | Format-Table LocalAddress, LocalPort, State, OwningProcess -AutoSize
