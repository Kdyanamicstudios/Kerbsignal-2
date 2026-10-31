$ErrorActionPreference='Stop'
try {
    [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
    $voice=New-Object -ComObject SAPI.SpVoice
    $tokens=$voice.GetVoices()
    $items=@()
    for ($i=0; $i -lt $tokens.Count; $i++) {
        $token=$tokens.Item($i)
        $language='';$gender=''
        try { $language=$token.GetAttribute('Language') } catch {}
        try { $gender=$token.GetAttribute('Gender') } catch {}
        $items += @{id=[string]$token.Id; name=[string]$token.GetDescription(); language=[string]$language; gender=[string]$gender}
    }
    [Console]::WriteLine((ConvertTo-Json -InputObject @($items) -Compress))
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
