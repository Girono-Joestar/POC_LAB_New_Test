# -------- CONFIG --------
$NgrokPath = "ngrok"              # or full path: C:\ngrok\ngrok.exe
$Domain    = "AI_Lab.ngrok-free.dev"
$Port      = 8501
$CheckHost = "8.8.8.8"            # Google DNS
$SleepSec  = 10
# ------------------------

Write-Host "🟢 Ngrok watchdog started..."

while ($true) {

    # Check internet connectivity
    $internetUp = Test-Connection -ComputerName $CheckHost -Count 1 -Quiet

    if ($internetUp) {

        # Check if ngrok is already running
        $ngrokRunning = Get-Process ngrok -ErrorAction SilentlyContinue

        if (-not $ngrokRunning) {
            Write-Host "🔄 Internet OK, starting ngrok..."
            Start-Process $NgrokPath -ArgumentList "http --domain=$Domain $Port"
        }
    }
    else {
        Write-Host "⚠️ Internet down, waiting..."
    }

    Start-Sleep -Seconds $SleepSec
}
