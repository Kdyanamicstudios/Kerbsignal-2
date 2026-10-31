$ErrorActionPreference = 'Stop'
try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    Add-Type -AssemblyName System.Speech
    $available = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
    $english = $available | Where-Object { $_.Culture.Name -like 'en-*' } | Select-Object -First 1
    if (-not $english) { throw 'Install an English Windows speech recognition language pack, then restart the app.' }
    $recognizer = [System.Speech.Recognition.SpeechRecognitionEngine]::new($english)
    $choices = [System.Speech.Recognition.Choices]::new()
    $choices.Add([string[]]@(
        'engineer what track am i on', 'engineer identify track', 'engineer where am i on track',
        'engineer what car am i driving', 'engineer identify my car',
        'engineer explain that', 'engineer session recap', 'engineer passing opportunities', 'engineer microphone check', 'engineer can you hear me', 'engineer last lap', 'engineer tires', 'engineer weather', 'engineer abs',
        'engineer traction control', 'engineer where am i losing time',
        'engineer compare line', 'engineer status', 'engineer setup',
        'engineer enable braking cues', 'engineer disable braking cues',
        'engineer play focus music', 'engineer start focus music', 'engineer open youtube', 'engineer mute', 'engineer unmute'
    ))
    $builder = [System.Speech.Recognition.GrammarBuilder]::new()
    $builder.Culture = $english.Culture
    $builder.Append($choices)
    $grammar = [System.Speech.Recognition.Grammar]::new($builder)
    $recognizer.LoadGrammar($grammar)
    $format = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $recognizer.SetInputToAudioStream([Console]::OpenStandardInput(), $format)
    [Console]::WriteLine('READY')
    while ($true) {
        $result = $recognizer.Recognize([TimeSpan]::FromSeconds(4))
        if ($null -ne $result -and $result.Confidence -ge 0.65) {
            [Console]::WriteLine('HEARD|' + $result.Confidence.ToString('F2', [System.Globalization.CultureInfo]::InvariantCulture) + '|' + $result.Text)
        }
    }
} catch {
    [Console]::WriteLine('ERROR: ' + $_.Exception.Message)
    exit 1
} finally {
    if ($null -ne $recognizer) { $recognizer.Dispose() }
}
