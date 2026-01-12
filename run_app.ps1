# PowerShell version of RUN script
Write-Host "Killing existing processes on ports 8000 and 5173..."
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $pids = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $pids) {
        Write-Host "Killing process $processId on port $port"
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 2

Write-Host "Starting backend server..."
$env:PYTHONPATH = $PSScriptRoot
Start-Process -NoNewWindow -FilePath "backend\venv\Scripts\python.exe" -ArgumentList "backend\main.py"

Start-Sleep -Seconds 5

Write-Host "Starting frontend server..."
npm run dev
