$ErrorActionPreference = 'Continue'
$urls = @(
    'http://127.0.0.1:8001/embed.js',
    'http://127.0.0.1:8001/widget.html'
)
foreach ($u in $urls) {
    Write-Host "=== $u ===" -ForegroundColor Cyan
    try {
        $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 5
        Write-Host ("Status: {0} {1}" -f $r.StatusCode, $r.StatusDescription)
        Write-Host ("Content-Length: {0}" -f $r.Content.Length)
        Write-Host ("Content-Type: {0}" -f $r.Headers['Content-Type'])
        Write-Host ""
        # Find iframe allow attr
        $matches = Select-String -InputObject $r.Content -Pattern 'iframe\.setAttribute|speech-recognition|microphone \*'
        foreach ($m in $matches) {
            Write-Host ("  L{0}: {1}" -f $m.LineNumber, $m.Line.Trim())
        }
        Write-Host ""
    } catch {
        Write-Host ("ERR: {0}" -f $_.Exception.Message) -ForegroundColor Red
    }
}
Write-Host "=== Local server health ===" -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 21732 } | Format-List Id, ProcessName, StartTime
