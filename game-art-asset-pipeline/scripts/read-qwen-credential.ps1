function Read-QwenCredential {
    param([string]$CredentialFile)
    try {
        $rows = @(Import-Csv -LiteralPath $CredentialFile -ErrorAction Stop)
        $keys = @($rows | ForEach-Object {
            $cells = @($_.PSObject.Properties.Value)
            if ($cells.Count -ge 2 -and ([string]$cells[0]).Trim() -match '^(?i:api[ _-]?key|key)$') {
                ([string]$cells[1]).Trim()
            }
        } | Where-Object { $_ } | Select-Object -Unique)
        if ($keys.Count -ne 1 -or $keys[0] -notmatch '^sk-\S+$') { throw 'Invalid credential structure' }
        return $keys[0]
    } catch { throw 'QWEN credential CSV unavailable or invalid; credential contents withheld.' }
}
