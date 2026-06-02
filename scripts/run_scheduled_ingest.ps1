# run_scheduled_ingest.ps1
# This script is intended to be called by Windows Task Scheduler or systems automation to refresh mutual fund details.
# Logs results to data/ingest_schedule.log

# Get current script path and project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath

# Change directory to project root
Set-Location $projectRoot

# Define log file
$logFile = Join-Path $projectRoot "data/ingest_schedule.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Write start log
"[$timestamp] Starting scheduled ingestion run..." | Out-File -FilePath $logFile -Append -Encoding utf8

try {
    # Check if virtual environment exists
    $venvPath = Join-Path $projectRoot ".venv"
    if (Test-Path $venvPath) {
        # Execute using venv python
        $pythonExe = Join-Path $venvPath "Scripts/python.exe"
        $output = & $pythonExe -m src.data.ingest 2>&1
        $status = $LASTEXITCODE
        
        $endTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        if ($status -eq 0) {
            "[$endTimestamp] Ingestion succeeded. Output:" | Out-File -FilePath $logFile -Append -Encoding utf8
            $output | Out-File -FilePath $logFile -Append -Encoding utf8
        } else {
            "[$endTimestamp] [ERROR] Ingestion failed with exit code $status. Output:" | Out-File -FilePath $logFile -Append -Encoding utf8
            $output | Out-File -FilePath $logFile -Append -Encoding utf8
        }
    } else {
        "[$timestamp] [ERROR] Virtual environment not found at $venvPath." | Out-File -FilePath $logFile -Append -Encoding utf8
    }
} catch {
    $endTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$endTimestamp] [ERROR] Unexpected exception occurred: $_" | Out-File -FilePath $logFile -Append -Encoding utf8
}

"----------------------------------------------------------------" | Out-File -FilePath $logFile -Append -Encoding utf8
