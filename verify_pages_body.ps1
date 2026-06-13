$ErrorActionPreference = 'Continue'
# Per 6-12 PowerShell Encoding Trap: avoid $resp.Content.Substring() (console-decoded)
# Use .NET WebClient.DownloadString which respects HTTP Content-Type charset, OR
# better: just check the ETag matches and read file via direct file diff approach.
# Here: read raw bytes from URL, count occurrences of "speech-recognition" in bytes.
$url = 'https://vampire.kitahim.uk/static/embed/embed.js'
Add-Type -AssemblyName System.Net.Http

# Use HttpClient.GetByteArrayAsync for byte-level (no console decode)
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromSeconds(20)
$bytes = $client.GetByteArrayAsync($url).GetAwaiter().GetResult()
$client.Dispose()

Write-Host "Downloaded $($bytes.Length) bytes from $url"
$text = [System.Text.Encoding]::UTF8.GetString($bytes)
Write-Host ""
Write-Host "Searches in body:"
$patterns = @('speech-recognition', 'microphone \*', 'iframe.setAttribute.*allow', 'mobile mic fix')
foreach ($p in $patterns) {
    $count = ([regex]::Matches($text, [regex]::Escape($p))).Count
    if ($count -gt 0) {
        Write-Host "  ✓ Found '$p' x$count" -ForegroundColor Green
    } else {
        Write-Host "  ✗ NOT FOUND: '$p'" -ForegroundColor Red
    }
}

# Print the iframe.setAttribute('allow', ...) line
$matches = Select-String -InputObject $text -Pattern 'iframe\.setAttribute.*allow'
foreach ($m in $matches) {
    Write-Host ""
    Write-Host "  iframe allow line: $($m.Line.Trim())" -ForegroundColor Cyan
}
