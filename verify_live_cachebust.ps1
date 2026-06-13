$ErrorActionPreference = 'Continue'
# Bypass any Cloudflare edge cache with cache-bust query string
Add-Type -AssemblyName System.Net.Http
$urls = @(
    'https://vampire.kitahim.uk/static/embed/embed.js?v=20260613v10',
    'https://vampire.kitahim.uk/static/embed/embed.js?cb=test123',
    'https://vampire.kitahim.uk/widget?v=20260613v10'
)
foreach ($u in $urls) {
    Write-Host "=== $u ===" -ForegroundColor Cyan
    try {
        $client = New-Object System.Net.Http.HttpClient
        $client.Timeout = [TimeSpan]::FromSeconds(20)
        $resp = $client.GetAsync($u, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
        Write-Host ("Status: {0} {1}" -f [int]$resp.StatusCode, $resp.ReasonPhrase)
        $resp.Headers | ForEach-Object {
            foreach ($v in $_.Value) {
                Write-Host ("  {0}: {1}" -f $_.Key, $v)
            }
        }
        $resp.Dispose()
        $client.Dispose()
    } catch {
        Write-Host ("ERR: {0}" -f $_.Exception.Message) -ForegroundColor Red
    }
    Write-Host ""
}
