$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Net.Http
$urls = @(
    'https://a984b7a3.vampire-widget.pages.dev/embed.js',
    'https://a984b7a3.vampire-widget.pages.dev/widget',
    'https://vampire-widget.pages.dev/embed.js',
    'https://vampire.kitahim.uk/static/embed/embed.js'
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
