$ErrorActionPreference = 'Continue'
$urls = @(
    'https://vampire.kitahim.uk/static/embed/embed.js',
    'https://vampire.kitahim.uk/widget'
)
foreach ($u in $urls) {
    Write-Host "=== $u ===" -ForegroundColor Cyan
    try {
        $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 15 -MaximumRedirection 5
        Write-Host ("Status: {0} {1}" -f $r.StatusCode, $r.StatusDescription)
        Write-Host ("FinalURL: {0}" -f $r.BaseResponse.RequestMessage.RequestUri)
        Write-Host ("Content-Length: {0}" -f $r.Content.Length)
        Write-Host ""
        # Find iframe allow attr
        $matches = Select-String -InputObject $r.Content -Pattern 'iframe\.setAttribute.*allow|speech-recognition|isIOS|isAndroid' -SimpleMatch:$false
        if ($matches) {
            foreach ($m in $matches) {
                Write-Host ("  Match: {0}" -f $m.Line.Trim())
            }
        } else {
            Write-Host "  (no matches found in body)" -ForegroundColor Yellow
        }
        Write-Host ""
    } catch {
        Write-Host ("ERR: {0}" -f $_.Exception.Message) -ForegroundColor Red
    }
}
