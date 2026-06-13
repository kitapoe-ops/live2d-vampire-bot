$ErrorActionPreference = 'Continue'
$r = Invoke-WebRequest -Uri 'https://vampire.kitahim.uk/static/embed/embed.js' -UseBasicParsing -TimeoutSec 15 -Method HEAD
Write-Host "=== embed.js HEAD ==="
Write-Host ("Status: {0}" -f $r.StatusCode)
$r.Headers | ForEach-Object {
    $k = $_.Key
    $v = $_.Value -join ', '
    Write-Host ("  {0}: {1}" -f $k, $v)
}
Write-Host ""
Write-Host "=== homepage headers ==="
$r2 = Invoke-WebRequest -Uri 'https://vampire.kitahim.uk/' -UseBasicParsing -TimeoutSec 15 -Method HEAD
$r2.Headers | ForEach-Object {
    $k = $_.Key
    $v = $_.Value -join ', '
    Write-Host ("  {0}: {1}" -f $k, $v)
}
