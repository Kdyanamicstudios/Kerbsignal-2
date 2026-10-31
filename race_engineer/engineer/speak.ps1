$ErrorActionPreference='Stop'
try {
    [Console]::InputEncoding=[System.Text.Encoding]::UTF8
    $data=[Console]::In.ReadToEnd() | ConvertFrom-Json
    $voice=New-Object -ComObject SAPI.SpVoice
    if ($data.voice_id) {
        $found=$null; $tokens=$voice.GetVoices()
        for ($i=0; $i -lt $tokens.Count; $i++) {
            $candidate=$tokens.Item($i)
            if ($candidate.Id -eq $data.voice_id) { $found=$candidate; break }
        }
        if (-not $found) { throw 'Selected SAPI voice is not installed or unavailable.' }
        $voice.Voice=$found
    }
    [void]$voice.Speak([string]$data.text)
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
