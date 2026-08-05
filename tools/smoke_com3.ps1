$port = New-Object System.IO.Ports.SerialPort 'COM3', 115200, 'None', 8, 'One'
$port.ReadTimeout = 3000
$port.WriteTimeout = 3000
$port.NewLine = "`n"
$port.Open()
$port.DiscardInBuffer()
$port.WriteLine('GET_LAST_ROW')
Start-Sleep -Milliseconds 500
try {
    $reply = $port.ReadLine()
    Write-Output "REPLY=$reply"
} catch {
    Write-Output "READ_ERR=$($_.Exception.Message)"
}
$port.Close()
