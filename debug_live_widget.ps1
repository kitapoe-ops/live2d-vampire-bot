$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Net.Http
$url = 'https://vampire.kitahim.uk/widget'
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromSeconds(20)
$bytes = $client.GetByteArrayAsync($url).GetAwaiter().GetResult()
$client.Dispose()
$text = [System.Text.Encoding]::UTF8.GetString($bytes)
Write-Host ("Downloaded {0} bytes from {1}" -f $bytes.Length, $url)
Write-Host ""

# Use a different var name to avoid PowerShell function keyword conflict
$patlist = @('isIOS', 'isAndroid', 'not-allowed', 'service-not-allowed', 'no-speech', 'Listening', 'MicAuth', 'startListening', 'speech-recognition', 'cantonese')
foreach ($p in $patlist) {
    $count = ([regex]::Matches($text, [regex]::Escape($p))).Count
    Write-Host ("  {0,-30}: x{1}" -f $p, $count)
}
Write-Host ""
Write-Host "--- startListening func body ---"
$idx = $text.IndexOf('startListening(')
if ($idx -ge 0) {
    $end = $text.IndexOf('function ', $idx + 30)
    if ($end -lt 0) { $end = $idx + 4000 }
    $snippet = $text.Substring($idx, [Math]::Min($end - $idx, 4000))
    Write-Host $snippet
}
