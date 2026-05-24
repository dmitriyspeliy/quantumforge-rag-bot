param(
    [string]$TaskName = "QuantumForgeRagDailyIndexUpdate",
    [string]$RunAt = "06:00"
)

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $ProjectRoot "scripts\update_index.py"

if (!(Test-Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

if (!(Test-Path $ScriptPath)) {
    throw "Update script not found: $ScriptPath"
}

$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At $RunAt

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Daily FAISS index update for QuantumForge RAG bot" `
    -Force

Write-Host "Task registered: $TaskName"
Write-Host "Schedule: daily at $RunAt"
Write-Host "Project root: $ProjectRoot"
