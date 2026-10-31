$ErrorActionPreference = 'Stop'
try {
    $data = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $clips = @($data.clips)
    $voice = New-Object -ComObject SAPI.SpVoice
    if ($data.voice_id) {
        $found=$null; $tokens=$voice.GetVoices()
        for ($i=0; $i -lt $tokens.Count; $i++) {
            $candidate=$tokens.Item($i)
            if ($candidate.Id -eq $data.voice_id) { $found=$candidate; break }
        }
        if (-not $found) { throw 'Selected SAPI voice is not installed or unavailable.' }
        $voice.Voice=$found
    }
    $voice.Rate = 2
    foreach ($clip in $clips) {
        $stream = New-Object -ComObject SAPI.SpFileStream
        try {
            $stream.Open([string]$clip.path, 3, $false)
            $voice.AudioOutputStream = $stream
            [void]$voice.Speak([string]$clip.text)
        } finally { $stream.Close() }
    }
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
