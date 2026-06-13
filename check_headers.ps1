Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromSeconds(15)
$urls = @(
    'https://vampire.kitahim.uk/widget',
    'https://vampire.kitahim.uk/embed.js',
    'https://a984b7a3.vampire-widget.pages.dev/widget'
)
foreach ($u in $urls) {
    Write-Host "=== $u ===" -ForegroundColor Cyan
    $r = $client.GetAsync($u).GetAwaiter().GetResult()
    Write-Host "Status: $($r.StatusCode)"
    $r.Headers | ForEach-Object {
        foreach ($v in $_.Value) {
            Write-Host "  $($_.Key): $v"
        }
    }
    Write-Host ""
}
$client.Dispose()
