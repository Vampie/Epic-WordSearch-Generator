setlocal EnableExtensions

set "INPUT=basiswoorden-gekeurd.txt"
set "OUTPUT=opentaal.txt"

if not exist "%INPUT%" (
  echo [FOUT] Bestand "%INPUT%" niet gevonden.
  exit /b 1
)

if exist "%OUTPUT%" del "%OUTPUT%"

rem Filter: exact 4 Unicode-letters (geen cijfers/punten), trim spaties, negeer lege regels.
powershell -NoProfile -ExecutionPolicy Bypass ^
  -Command ^
  "$ErrorActionPreference='Stop';" ^
  "(Get-Content -LiteralPath '%INPUT%' -Encoding UTF8) |" ^
  "ForEach-Object { $_.Trim() } |" ^
  "Where-Object { $_ -ne '' -and $_ -match '^[\p{L}]{4}$' } |" ^
  "Set-Content -LiteralPath '%OUTPUT%' -Encoding UTF8"

if errorlevel 1 (
  echo [FOUT] Tijdens het filteren trad een fout op.
  exit /b 1
)

echo [OK] Gereed. Resultaat staat in "%OUTPUT%".
endlocal

pause