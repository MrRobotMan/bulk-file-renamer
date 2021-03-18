param (
    [string]$path = $(Get-Location)
)
& $PSScriptRoot\.env\scripts\python.exe $PSScriptRoot\rename.py $path