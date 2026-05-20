param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "restart", "status")]
    [string]$Command = "up"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateDir = Join-Path $RepoRoot ".dev"
$PidFile = Join-Path $StateDir "pids.json"
$BackendOutLog = Join-Path $StateDir "backend.out.log"
$BackendErrLog = Join-Path $StateDir "backend.err.log"
$FrontendOutLog = Join-Path $StateDir "frontend.out.log"
$FrontendErrLog = Join-Path $StateDir "frontend.err.log"

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
        backend_out_log  = $BackendOutLog
        backend_err_log  = $BackendErrLog
        frontend_out_log = $FrontendOutLog
        frontend_err_log = $FrontendErrLog
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
        $proc = Get-Process -Id $ProcessId -ErrorAction Stop
        # Guard against PID reuse (don't kill unrelated processes like notepad).
        if ($Name -eq "backend" -and $proc.ProcessName -notlike "python*") {
            Write-Warning "Refusing to stop PID $ProcessId for backend; found process '$($proc.ProcessName)'. PID reuse likely."
            return
        }
        if ($Name -eq "frontend" -and $proc.ProcessName -notin @("cmd", "node", "npm")) {
            Write-Warning "Refusing to stop PID $ProcessId for frontend; found process '$($proc.ProcessName)'. PID reuse likely."
            return
        }

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

function Get-ListeningPids([int]$Port) {
    $pids = New-Object System.Collections.Generic.HashSet[int]
    try {
        $pattern = "^\\s*TCP\\s+\\S+:$Port\\s+\\S+\\s+LISTENING\\s+(\\d+)\\s*$"
        $matchInfos = netstat -ano -p TCP 2>$null | Select-String -Pattern $pattern
        foreach ($m in $matchInfos) {
            if ($m.Line -match $pattern) {
                [void]$pids.Add([int]$Matches[1])
            }
        }
    }
    catch {
        return @()
    }
    return @($pids | Sort-Object)
}

function Start-Backend {
    $backendDir = Join-Path $RepoRoot "backend"
    $python = Get-BackendPython
    $env:DJANGO_SETTINGS_MODULE = "config.settings.development"

    $args = @("manage.py", "runserver", "127.0.0.1:8000")
    Ensure-StateDir
    $proc = Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $BackendOutLog -RedirectStandardError $BackendErrLog
    Write-Host "Started backend (PID $($proc.Id)) at http://127.0.0.1:8000"
    return $proc.Id
}

function Start-Frontend {
    $frontendDir = Join-Path $RepoRoot "frontend"

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) {
        throw "npm not found. Install Node.js first."
    }

    Ensure-StateDir
    # Use cmd.exe to run npm.cmd reliably on Windows and keep a single parent PID to stop.
    $proc = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm", "run", "dev") -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $FrontendOutLog -RedirectStandardError $FrontendErrLog
    Write-Host "Started frontend (PID $($proc.Id)) at http://127.0.0.1:3000"
    return $proc.Id
}

function Wait-ForHttp([string]$Url, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $null = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 3 -UseBasicParsing
            return $true
        }
        catch {
            Start-Sleep -Milliseconds 300
        }
    }
    return $false
}

function Up {
    $pids = Read-Pids
    if ($pids -and (Is-Running $pids.backend_pid -or Is-Running $pids.frontend_pid)) {
        Write-Host "Already running. Use: .\\dev.ps1 restart"
        return
    }

    $existingBackend = Get-ListeningPids -Port 8000
    if ($existingBackend.Count -gt 0) {
        throw "Port 8000 is already in use (PID(s) $($existingBackend -join ', ')). Stop it first (try: .\\dev.cmd down)."
    }

    $existingFrontend = Get-ListeningPids -Port 3000
    if ($existingFrontend.Count -gt 0) {
        throw "Port 3000 is already in use (PID(s) $($existingFrontend -join ', ')). Stop it first (try: .\\dev.cmd down)."
    }

    $backendPid = Start-Backend
    $frontendPid = Start-Frontend
    Write-Pids -BackendPid $backendPid -FrontendPid $frontendPid

    if (-not (Wait-ForHttp -Url "http://127.0.0.1:8000/api/v1/health/live/" -TimeoutSeconds 20)) {
        Write-Warning "Backend didn't become ready. Check logs: $BackendOutLog / $BackendErrLog"
        Down
        throw "Backend failed to start."
    }

    if (-not (Wait-ForHttp -Url "http://127.0.0.1:3000/healthz" -TimeoutSeconds 40)) {
        Write-Warning "Frontend didn't become ready. Check logs: $FrontendOutLog / $FrontendErrLog"
        Down
        throw "Frontend failed to start."
    }

    # Update PID file with actual listening processes (avoids killing a wrapper cmd.exe PID and missing node/python).
    $backendListenPids = Get-ListeningPids -Port 8000
    $frontendListenPids = Get-ListeningPids -Port 3000
    if ($backendListenPids.Count -gt 0 -and $frontendListenPids.Count -gt 0) {
        Write-Pids -BackendPid ([int]$backendListenPids[0]) -FrontendPid ([int]$frontendListenPids[0])
    }
}

function Down {
    $pids = Read-Pids
    if (-not $pids) {
        Write-Host "No PID file found ($PidFile). Nothing to stop."
        # Still try to stop listeners if they exist.
        $frontPids = Get-ListeningPids -Port 3000
        $backPids = Get-ListeningPids -Port 8000
        if ($frontPids.Count -gt 0) { Write-Host "Found frontend listeners on 3000: $($frontPids -join ', ')" }
        if ($backPids.Count -gt 0) { Write-Host "Found backend listeners on 8000: $($backPids -join ', ')" }
        foreach ($fp in $frontPids) { Stop-IfRunning -ProcessId $fp -Name "frontend" }
        foreach ($bp in $backPids) { Stop-IfRunning -ProcessId $bp -Name "backend" }
        return
    }

    Stop-IfRunning -ProcessId $pids.frontend_pid -Name "frontend"
    Stop-IfRunning -ProcessId $pids.backend_pid -Name "backend"
    # In case wrapper PIDs were stored, also stop current listeners.
    foreach ($fp2 in (Get-ListeningPids -Port 3000)) { Stop-IfRunning -ProcessId $fp2 -Name "frontend" }
    foreach ($bp2 in (Get-ListeningPids -Port 8000)) { Stop-IfRunning -ProcessId $bp2 -Name "backend" }
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
