<#
TA-052 · Regresión final y escaneo de secretos (Castro).

Corre, desde la raíz del repositorio y con el venv activado:
  1. pytest completo (con PostgreSQL si DATABASE_URL está definido)
  2. Playwright en modo demostración (frontend/e2e)
  3. Playwright contra la API real o producción (opcional: -ApiUrl o -FrontUrl)
  4. gitleaks sobre todo el historial
y guarda los reportes en docs/sprint2/evidencias/TA-052/.

Uso:
  .\scripts\ta052_regresion_final.ps1
  .\scripts\ta052_regresion_final.ps1 -FrontUrl https://<frontend> -Proyecto "Proyecto demo Grupo 8"
Las credenciales del docente de prueba van en $env:E2E_CORREO y $env:E2E_CLAVE (no en el script).
#>
param(
  [string]$ApiUrl = "",
  [string]$FrontUrl = "",
  [string]$Proyecto = ""
)
$ErrorActionPreference = "Continue"
$raiz = Split-Path -Parent $PSScriptRoot
$salida = Join-Path $raiz "docs\sprint2\evidencias\TA-052"
New-Item -ItemType Directory -Force -Path $salida | Out-Null
$resumen = [ordered]@{}

Write-Host "1/4 pytest" -ForegroundColor Cyan
Push-Location $raiz
python -m pytest -q --junitxml="$salida\pytest.xml" 2>&1 | Tee-Object "$salida\pytest.txt"
$resumen["pytest"] = if ($LASTEXITCODE -eq 0) { "OK" } else { "FALLA" }
Pop-Location

Write-Host "2/4 Playwright (demostración)" -ForegroundColor Cyan
Push-Location (Join-Path $raiz "frontend")
npx playwright test --reporter=list 2>&1 | Tee-Object "$salida\playwright_demo.txt"
$resumen["playwright_demo"] = if ($LASTEXITCODE -eq 0) { "OK" } else { "FALLA" }
if (Test-Path playwright-report) { Copy-Item -Recurse -Force playwright-report "$salida\playwright-report-demo" }

if ($ApiUrl -or $FrontUrl) {
  Write-Host "3/4 Playwright contra la API" -ForegroundColor Cyan
  if ($ApiUrl) { $env:E2E_API_URL = $ApiUrl; $env:VITE_API_URL = $ApiUrl }
  if ($FrontUrl) { $env:E2E_FRONT_URL = $FrontUrl }
  if ($Proyecto) { $env:E2E_PROYECTO = $Proyecto }
  npx playwright test -c playwright.api.config.js --reporter=list 2>&1 | Tee-Object "$salida\playwright_api.txt"
  $resumen["playwright_api"] = if ($LASTEXITCODE -eq 0) { "OK" } else { "FALLA" }
  if (Test-Path playwright-report-api) { Copy-Item -Recurse -Force playwright-report-api "$salida\playwright-report-api" }
} else {
  $resumen["playwright_api"] = "omitido (sin -ApiUrl ni -FrontUrl)"
}
Pop-Location

Write-Host "4/4 gitleaks" -ForegroundColor Cyan
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
  Push-Location $raiz
  gitleaks detect --source . --report-format json --report-path "$salida\gitleaks.json" --redact 2>&1 | Tee-Object "$salida\gitleaks.txt"
  $resumen["gitleaks"] = if ($LASTEXITCODE -eq 0) { "OK (sin hallazgos)" } else { "HALLAZGOS: revisar gitleaks.json" }
  Pop-Location
} else {
  $resumen["gitleaks"] = "no instalado (winget install gitleaks.gitleaks)"
}

$resumen["fecha"] = (Get-Date -Format "yyyy-MM-dd HH:mm")
$resumen["commit"] = (git -C $raiz rev-parse --short HEAD)
$resumen | ConvertTo-Json | Set-Content -Encoding utf8 "$salida\resumen.json"
Write-Host ""
$resumen.GetEnumerator() | ForEach-Object { Write-Host ("{0,-16} {1}" -f $_.Key, $_.Value) }
Write-Host "Reportes en $salida"
