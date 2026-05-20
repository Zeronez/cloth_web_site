param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "restart", "status")]
    [string]$Command = "up"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateDir = Join-Path $RepoRoot ".dev"
$PidFile = Join-Path $StateDir "pids.json"

function Ensure-StateDir {
    if (-not (Test-Path $StateDir)) {
        New-Item -ItemType Directory -Path $StateDir | Out-Null
    }
}

function Read-Pids {
    if (-not (Test-Path $PidFile)) {
        return $null
    }
    try {
        return (Get-Content -Raw $PidFile | ConvertFrom-Json)
    }
    catch {
        return $null
    }
}

function Write-Pids([int]$BackendPid, [int]$FrontendPid) {
    Ensure-StateDir
    $obj = [pscustomobject]@{
        backend_pid  = $BackendPid
        frontend_pid = $FrontendPid
        started_at   = (Get-Date).ToString("o")
    }
    $obj | ConvertTo-Json | Set-Content -Encoding UTF8 $PidFile
}

function Is-Running([int]$ProcessId) {
    if (-not $ProcessId) { return $false }
    try {
        $p = Get-Process -Id $ProcessId -ErrorAction Stop
        return ($null -ne $p)
    }
    catch {
        return $false
    }
}

function Stop-IfRunning([int]$ProcessId, [string]$Name) {
    if (-not $ProcessId) { return }
    if (-not (Is-Running $ProcessId)) { return }
    try {
        Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        Write-Host "Stopped $Name (PID $ProcessId)"
    }
    catch {
        Write-Warning "Failed to stop $Name (PID $ProcessId): $($_.Exception.Message)"
    }
}

function Get-BackendPython {
    $venvPython = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    return "python"
}

function Start-Backend {
    $backendDir = Join-Path $RepoRoot "backend"
    $python = Get-BackendPython
    $env:DJANGO_SETTINGS_MODULE = "config.settings.development"

    $args = @("manage.py", "runserver", "127.0.0.1:8000")
    $proc = Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru
    Write-Host "Started backend (PID $($proc.Id)) at http://127.0.0.1:8000"
    return $proc.Id
}

function Start-Frontend {
    $frontendDir = Join-Path $RepoRoot "frontend"

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) {
        throw "npm not found. Install Node.js first."
    }

    $proc = Start-Process -FilePath $npm.Source -ArgumentList @("run", "dev") -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru
    Write-Host "Started frontend (PID $($proc.Id)) at http://127.0.0.1:3000"
    return $proc.Id
}

function Up {
    $pids = Read-Pids
    if ($pids -and (Is-Running $pids.backend_pid -or Is-Running $pids.frontend_pid)) {
        Write-Host "Already running. Use: .\\dev.ps1 restart"
        return
    }

    $backendPid = Start-Backend
    Start-Sleep -Milliseconds 300
    $frontendPid = Start-Frontend
    Write-Pids -BackendPid $backendPid -FrontendPid $frontendPid
}

function Down {
    $pids = Read-Pids
    if (-not $pids) {
        Write-Host "No PID file found ($PidFile). Nothing to stop."
        return
    }

    Stop-IfRunning -ProcessId $pids.frontend_pid -Name "frontend"
    Stop-IfRunning -ProcessId $pids.backend_pid -Name "backend"
    Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
}

function Status {
    $pids = Read-Pids
    if (-not $pids) {
        Write-Host "Not running (no PID file)."
        return
    }

    $b = Is-Running $pids.backend_pid
    $f = Is-Running $pids.frontend_pid
    Write-Host ("backend  PID {0} : {1}" -f $pids.backend_pid, ($(if ($b) { "running" } else { "stopped" })))
    Write-Host ("frontend PID {0} : {1}" -f $pids.frontend_pid, ($(if ($f) { "running" } else { "stopped" })))
}

switch ($Command) {
    "up" { Up }
    "down" { Down }
    "restart" { Down; Up }
    "status" { Status }
}
