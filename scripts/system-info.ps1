# Proje klasöründe: powershell -File scripts/system-info.ps1
# Seri numarası, kullanıcı adı ve ağ adresi toplamaz; kurulum yapmaz.
$ErrorActionPreference = "Stop"
$ragRoot = Split-Path -Parent $PSScriptRoot
$ragOS = Get-CimInstance Win32_OperatingSystem
$ragComputer = Get-CimInstance Win32_ComputerSystem
$ragCPU = Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name
$ragGPU = Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name
[pscustomobject]@{
    Windows = $ragOS.Caption
    Version = $ragOS.Version
    Architecture = $ragOS.OSArchitecture
    RAM_GB = [math]::Round($ragComputer.TotalPhysicalMemory / 1GB, 1)
    CPU = @($ragCPU)
    GPU = @($ragGPU)
} | ConvertTo-Json
$ragNvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($ragNvidia) {
    & $ragNvidia.Source --query-gpu=name,memory.total,driver_version --format=csv,noheader
    if ($LASTEXITCODE -ne 0) {
        Write-Output "nvidia-smi failed; share its error output."
    }
} else {
    Write-Output "nvidia-smi not found; NVIDIA driver and VRAM are not verified."
}
$ragPython = Join-Path $ragRoot ".venv\Scripts\python.exe"
if (Test-Path $ragPython) {
    & $ragPython (Join-Path $ragRoot "main.py") doctor
    if ($LASTEXITCODE -ne 0) { throw "Python tanılama başarısız." }
} else {
    Write-Output "Proje sanal ortamı henüz yok. README'deki ilk kurulum adımlarını izleyin."
}
