$ErrorActionPreference = 'Continue'
# 2026-06-12 PowerShell Encoding Trap fix: do NOT use .Content (gets console-decoded)
# Read response headers via response.Headers collection (raw, not text-decoded)
$urls = @(
    'https://vampire.kitahim.uk/',
    'https://vampire.kitahim.uk/static/embed/embed.js',
    'https://vampire.kitahim.uk/widget'
)
foreach ($u in $urls) {
    Write-Host "=== $u ===" -ForegroundColor Cyan
    try {
        # Use HttpClient for raw header access (no .Content decoding)
        Add-Type -AssemblyName System.Net.Http
        $client = New-Object System.Net.Http.HttpClient
        $client.Timeout = [TimeSpan]::FromSeconds(15)
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
