# Backfill script for Windows PowerShell
# Chạy tuần tự từng ngày với delay để tránh BigQuery rate limit

$startDate = Get-Date "2026-06-01"
$endDate = Get-Date "2026-06-30"
$currentDate = $startDate

Write-Host "=== Starting Backfill ===" -ForegroundColor Green
Write-Host "From: $($startDate.ToString('yyyy-MM-dd'))" -ForegroundColor Cyan
Write-Host "To: $($endDate.ToString('yyyy-MM-dd'))" -ForegroundColor Cyan
Write-Host ""

while ($currentDate -le $endDate) {
    $dateStr = $currentDate.ToString("yyyy-MM-dd")
    Write-Host "[$dateStr] Triggering DAG..." -ForegroundColor Yellow
    
    # Trigger DAG cho ngày hiện tại
    docker exec -it airflow_scheduler airflow dags trigger `
        crypto_price_tracking_batch `
        -e $dateStr
    
    Write-Host "[$dateStr] Waiting 60 seconds to avoid rate limit..." -ForegroundColor Gray
    Start-Sleep -Seconds 60
    
    # Move to next day
    $currentDate = $currentDate.AddDays(1)
}

Write-Host ""
Write-Host "=== Backfill Complete! ===" -ForegroundColor Green