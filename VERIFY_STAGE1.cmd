@echo off
setlocal
cd /d "%~dp0"
echo Verifying Stage 1 package paths and exact file hashes. No downloads or changes.
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; try { $lines=Get-Content -LiteralPath 'STAGE1_CHECKSUMS.sha256'; $count=0; foreach($line in $lines) { if($line -notmatch '^([a-f0-9]{64})  (.+)$') {throw 'Malformed checksum manifest'}; $expected=$Matches[1]; $relative=$Matches[2]; if($relative.Contains('..') -or [IO.Path]::IsPathRooted($relative)) {throw 'Unsafe manifest path'}; if(-not(Test-Path -LiteralPath $relative -PathType Leaf)){throw ('Missing file: '+$relative)}; $actual=(Get-FileHash -LiteralPath $relative -Algorithm SHA256).Hash.ToLower(); if($actual -ne $expected){throw ('Hash mismatch: '+$relative)}; $count++ }; if($count -eq 0){throw 'Empty manifest'}; Write-Host ('PASS: '+$count+' Stage 1 files have correct paths and bytes.'); exit 0 } catch { Write-Host ('STOP: '+$_.Exception.Message); exit 1 }"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo Do not commit. Send the STOP message to the assistant.
pause
exit /b %RESULT%
