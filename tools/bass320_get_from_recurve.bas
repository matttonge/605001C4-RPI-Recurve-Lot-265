Attribute VB_Name = "RecurveUsbTransfer"
'
' Import into Bass-320 template:
'   Developer → Visual Basic → File → Import File… → bass320_get_from_recurve.bas
' Buttons:
'   GetFromRecurve     — USB COM (default COM3)
'   GetFromRecurveWifi — Wi-Fi HTTP using IP in active sheet AA1 (port 8765)
'
' COM port config (first match wins):
'   1) Worksheet "Config" cell B2  (recommended: put COM3 there)
'   2) Active sheet cell Z1
'   3) DEFAULT_COM_PORT below
'
' Wi-Fi IP: active sheet cell AA1 (e.g. 192.168.1.186)
'
' Protocol (USB @ 115200 8N1, or Wi-Fi GET /last_row):
'   PC → Pi: GET_LAST_ROW\n   (USB)  or  GET http://ip:8765/last_row
'   Pi → PC: OK\tv1\tv2\t...\tv8\n  or  ERR\tmessage\n
' Values are written to columns C–J of the selected row (data rows start at 26).

Option Explicit

Private Const DEFAULT_COM_PORT As String = "COM3"
Private Const DEFAULT_BAUD As Long = 115200
Private Const DEFAULT_WIFI_PORT As Long = 8765
Private Const FIRST_DATA_ROW As Long = 26
Private Const COL_C As Long = 3
Private Const FIELD_COUNT As Long = 8
Private Const WIFI_IP_CELL As String = "AA1"

Private Const GENERIC_READ As Long = &H80000000
Private Const GENERIC_WRITE As Long = &H40000000
Private Const OPEN_EXISTING As Long = 3
Private Const FILE_ATTRIBUTE_NORMAL As Long = &H80
Private Const PURGE_RXCLEAR As Long = &H8
Private Const PURGE_TXCLEAR As Long = &H4

Private Type DCB
    DCBlength As Long
    BaudRate As Long
    fBitFields As Long
    wReserved As Integer
    XonLim As Integer
    XoffLim As Integer
    ByteSize As Byte
    Parity As Byte
    StopBits As Byte
    XonChar As Byte
    XoffChar As Byte
    ErrorChar As Byte
    EofChar As Byte
    EvtChar As Byte
    wReserved1 As Integer
End Type

Private Type COMMTIMEOUTS
    ReadIntervalTimeout As Long
    ReadTotalTimeoutMultiplier As Long
    ReadTotalTimeoutConstant As Long
    WriteTotalTimeoutMultiplier As Long
    WriteTotalTimeoutConstant As Long
End Type

#If VBA7 Then
Private Declare PtrSafe Function CreateFileA Lib "kernel32" (ByVal lpFileName As String, ByVal dwDesiredAccess As Long, ByVal dwShareMode As Long, ByVal lpSecurityAttributes As LongPtr, ByVal dwCreationDisposition As Long, ByVal dwFlagsAndAttributes As Long, ByVal hTemplateFile As LongPtr) As LongPtr
Private Declare PtrSafe Function CloseHandle Lib "kernel32" (ByVal hObject As LongPtr) As Long
Private Declare PtrSafe Function WriteFile Lib "kernel32" (ByVal hFile As LongPtr, ByVal lpBuffer As LongPtr, ByVal nNumberOfBytesToWrite As Long, ByRef lpNumberOfBytesWritten As Long, ByVal lpOverlapped As LongPtr) As Long
Private Declare PtrSafe Function ReadFile Lib "kernel32" (ByVal hFile As LongPtr, ByVal lpBuffer As LongPtr, ByVal nNumberOfBytesToRead As Long, ByRef lpNumberOfBytesRead As Long, ByVal lpOverlapped As LongPtr) As Long
Private Declare PtrSafe Function SetCommState Lib "kernel32" (ByVal hFile As LongPtr, ByRef lpDCB As DCB) As Long
Private Declare PtrSafe Function GetCommState Lib "kernel32" (ByVal hFile As LongPtr, ByRef lpDCB As DCB) As Long
Private Declare PtrSafe Function SetCommTimeouts Lib "kernel32" (ByVal hFile As LongPtr, ByRef lpCommTimeouts As COMMTIMEOUTS) As Long
Private Declare PtrSafe Function PurgeComm Lib "kernel32" (ByVal hFile As LongPtr, ByVal dwFlags As Long) As Long
Private Declare PtrSafe Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As Long)
#Else
Private Declare Function CreateFileA Lib "kernel32" (ByVal lpFileName As String, ByVal dwDesiredAccess As Long, ByVal dwShareMode As Long, ByVal lpSecurityAttributes As Long, ByVal dwCreationDisposition As Long, ByVal dwFlagsAndAttributes As Long, ByVal hTemplateFile As Long) As Long
Private Declare Function CloseHandle Lib "kernel32" (ByVal hObject As Long) As Long
Private Declare Function WriteFile Lib "kernel32" (ByVal hFile As Long, ByVal lpBuffer As Long, ByVal nNumberOfBytesToWrite As Long, ByRef lpNumberOfBytesWritten As Long, ByVal lpOverlapped As Long) As Long
Private Declare Function ReadFile Lib "kernel32" (ByVal hFile As Long, ByVal lpBuffer As Long, ByVal nNumberOfBytesToRead As Long, ByRef lpNumberOfBytesRead As Long, ByVal lpOverlapped As Long) As Long
Private Declare Function SetCommState Lib "kernel32" (ByVal hFile As Long, ByRef lpDCB As DCB) As Long
Private Declare Function GetCommState Lib "kernel32" (ByVal hFile As Long, ByRef lpDCB As DCB) As Long
Private Declare Function SetCommTimeouts Lib "kernel32" (ByVal hFile As Long, ByRef lpCommTimeouts As COMMTIMEOUTS) As Long
Private Declare Function PurgeComm Lib "kernel32" (ByVal hFile As Long, ByVal dwFlags As Long) As Long
Private Declare Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As Long)
#End If

Public Sub GetFromRecurve()
    Dim portName As String
    Dim reply As String
    Dim targetRow As Long
    Dim ws As Worksheet

    On Error GoTo Fail
    Set ws = ActiveSheet
    portName = ReadComPort(ws)
    targetRow = ActiveCell.Row

    If targetRow < FIRST_DATA_ROW Then
        MsgBox "Select a Bass-320 data row (row " & CStr(FIRST_DATA_ROW) & _
               " or below), then click Get from Recurve.", vbExclamation, "Recurve"
        Exit Sub
    End If

    reply = QueryRecurve(portName, DEFAULT_BAUD, "GET_LAST_ROW")
    If Len(Trim$(reply)) = 0 Then
        MsgBox "No response from Recurve on " & portName & "." & vbCrLf & _
               "Check USB cable, Pi Setup → Enable USB Transfer → Connect, and COM port.", _
               vbCritical, "Recurve"
        Exit Sub
    End If

    ApplyReplyToRow ws, targetRow, reply
    Exit Sub

Fail:
    Application.ScreenUpdating = True
    MsgBox "Get from Recurve failed: " & Err.Description, vbCritical, "Recurve"
End Sub

Public Sub GetFromRecurveWifi()
    Dim ipAddr As String
    Dim reply As String
    Dim targetRow As Long
    Dim ws As Worksheet

    On Error GoTo Fail
    Set ws = ActiveSheet
    ipAddr = ReadWifiIp(ws)
    targetRow = ActiveCell.Row

    If targetRow < FIRST_DATA_ROW Then
        MsgBox "Select a Bass-320 data row (row " & CStr(FIRST_DATA_ROW) & _
               " or below), then click Get from Recurve (Wi-Fi).", vbExclamation, "Recurve"
        Exit Sub
    End If

    If Len(ipAddr) = 0 Then
        MsgBox "Put the Pi IP address in cell " & WIFI_IP_CELL & _
               " (e.g. 192.168.1.186), then try again.", vbExclamation, "Recurve"
        Exit Sub
    End If

    reply = QueryRecurveWifi(ipAddr, DEFAULT_WIFI_PORT)
    If Len(Trim$(reply)) = 0 Then
        MsgBox "No response from Recurve at http://" & ipAddr & ":" & _
               CStr(DEFAULT_WIFI_PORT) & "/last_row" & vbCrLf & _
               "Check Wi-Fi, Pi Setup → Enable Wi-Fi Transfer → Connect, and " & _
               WIFI_IP_CELL & ".", vbCritical, "Recurve"
        Exit Sub
    End If

    ApplyReplyToRow ws, targetRow, reply
    Exit Sub

Fail:
    Application.ScreenUpdating = True
    MsgBox "Get from Recurve (Wi-Fi) failed: " & Err.Description, vbCritical, "Recurve"
End Sub

Private Sub ApplyReplyToRow(ByVal ws As Worksheet, ByVal targetRow As Long, ByVal reply As String)
    Dim parts() As String
    Dim i As Long

    parts = Split(reply, vbTab)
    If UBound(parts) < 1 Then
        MsgBox "Bad response:" & vbCrLf & reply, vbCritical, "Recurve"
        Exit Sub
    End If

    If UCase$(Trim$(parts(0))) = "ERR" Then
        If UBound(parts) >= 1 Then
            MsgBox "Recurve error: " & parts(1), vbExclamation, "Recurve"
        Else
            MsgBox "Recurve error.", vbExclamation, "Recurve"
        End If
        Exit Sub
    End If

    If UCase$(Trim$(parts(0))) <> "OK" Or UBound(parts) < FIELD_COUNT Then
        MsgBox "Unexpected response:" & vbCrLf & reply, vbCritical, "Recurve"
        Exit Sub
    End If

    Application.ScreenUpdating = False
    For i = 1 To FIELD_COUNT
        ws.Cells(targetRow, COL_C + i - 1).Value = parts(i)
    Next i
    Application.ScreenUpdating = True
End Sub

Private Function ReadWifiIp(ByVal ws As Worksheet) As String
    Dim v As Variant
    v = ws.Range(WIFI_IP_CELL).Value
    ReadWifiIp = Trim$(CStr(v & ""))
End Function

Private Function QueryRecurveWifi(ByVal ipAddr As String, ByVal port As Long) As String
    Dim http As Object
    Dim url As String
    Dim status As Long
    Dim body As String

    url = "http://" & ipAddr & ":" & CStr(port) & "/last_row"
    Set http = CreateObject("WinHttp.WinHttpRequest.5.1")
    http.SetTimeouts 2000, 2000, 3000, 3000
    http.Open "GET", url, False
    http.Send
    status = CLng(http.Status)
    body = CStr(http.ResponseText)
    If status < 200 Or status >= 300 Then
        If Len(Trim$(body)) = 0 Then
            Err.Raise vbObjectError + 2001, , "HTTP " & CStr(status)
        End If
    End If
    QueryRecurveWifi = FirstLine(body)
End Function

Private Function ReadComPort(ByVal ws As Worksheet) As String
    Dim cfg As Worksheet
    Dim v As Variant

    On Error Resume Next
    Set cfg = ThisWorkbook.Worksheets("Config")
    On Error GoTo 0

    If Not cfg Is Nothing Then
        v = cfg.Range("B2").Value
        If Len(Trim$(CStr(v & ""))) > 0 Then
            ReadComPort = UCase$(Trim$(CStr(v)))
            Exit Function
        End If
    End If

    v = ws.Range("Z1").Value
    If Len(Trim$(CStr(v & ""))) > 0 Then
        ReadComPort = UCase$(Trim$(CStr(v)))
        Exit Function
    End If

    ReadComPort = DEFAULT_COM_PORT
End Function

Private Function QueryRecurve(ByVal portName As String, ByVal baud As Long, ByVal command As String) As String
    On Error Resume Next
    Dim ms As Object
    Set ms = CreateObject("MSCOMMLib.MSComm")
    On Error GoTo 0

    If Not ms Is Nothing Then
        QueryRecurve = QueryViaMsComm(ms, portName, baud, command)
    Else
        QueryRecurve = FirstLine(QueryViaWin32(portName, baud, command))
    End If
End Function

Private Function QueryViaMsComm(ByVal ms As Object, ByVal portName As String, ByVal baud As Long, ByVal command As String) As String
    Dim t0 As Single
    Dim raw As String
    Dim comNum As String

    comNum = Replace(UCase$(portName), "COM", "")
    ms.CommPort = CInt(comNum)
    ms.Settings = CStr(baud) & ",N,8,1"
    ms.InputLen = 0
    ms.PortOpen = True
    ms.Output = command & vbLf
    t0 = Timer
    Do While Timer < t0 + 2#
        DoEvents
        If ms.InBufferCount > 0 Then Exit Do
    Loop
    raw = CStr(ms.Input)
    ms.PortOpen = False
    QueryViaMsComm = FirstLine(raw)
End Function

Private Function QueryViaWin32(ByVal portName As String, ByVal baud As Long, ByVal command As String) As String
    Dim path As String
    Dim dcbx As DCB
    Dim tmo As COMMTIMEOUTS
    Dim written As Long
    Dim nRead As Long
    Dim outBytes() As Byte
    Dim inBytes() As Byte
    Dim accumulated As String
    Dim i As Long
    Dim chunk As String
#If VBA7 Then
    Dim h As LongPtr
#Else
    Dim h As Long
#End If

    path = "\\.\" & UCase$(portName)
    h = CreateFileA(path, GENERIC_READ Or GENERIC_WRITE, 0, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0)
    If h = -1 Or h = 0 Then Err.Raise vbObjectError + 1001, , "Cannot open " & portName

    On Error GoTo CleanFail
    dcbx.DCBlength = LenB(dcbx)
    If GetCommState(h, dcbx) = 0 Then Err.Raise vbObjectError + 1002, , "GetCommState failed"
    dcbx.BaudRate = baud
    dcbx.ByteSize = 8
    dcbx.Parity = 0
    dcbx.StopBits = 0
    If SetCommState(h, dcbx) = 0 Then Err.Raise vbObjectError + 1003, , "SetCommState failed"

    tmo.ReadIntervalTimeout = 50
    tmo.ReadTotalTimeoutConstant = 1500
    tmo.WriteTotalTimeoutConstant = 1000
    SetCommTimeouts h, tmo
    PurgeComm h, PURGE_RXCLEAR Or PURGE_TXCLEAR

    outBytes = StrConv(command & vbLf, vbFromUnicode)
    If WriteFile(h, VarPtr(outBytes(0)), UBound(outBytes) + 1, written, 0) = 0 Then
        Err.Raise vbObjectError + 1004, , "WriteFile failed"
    End If

    accumulated = ""
    ReDim inBytes(0 To 255)
    For i = 1 To 40
        nRead = 0
        If ReadFile(h, VarPtr(inBytes(0)), 256, nRead, 0) <> 0 Then
            If nRead > 0 Then
                chunk = BytesToAscii(inBytes, nRead)
                accumulated = accumulated & chunk
                If InStr(accumulated, vbLf) > 0 Or InStr(accumulated, vbCr) > 0 Then Exit For
            End If
        End If
        Sleep 25
    Next i

    CloseHandle h
    QueryViaWin32 = accumulated
    Exit Function

CleanFail:
    If h <> 0 And h <> -1 Then CloseHandle h
    Err.Raise Err.Number, Err.Source, Err.Description
End Function

Private Function BytesToAscii(ByRef buf() As Byte, ByVal n As Long) As String
    Dim i As Long
    Dim s As String
    s = ""
    For i = 0 To n - 1
        s = s & Chr$(buf(i))
    Next i
    BytesToAscii = s
End Function

Private Function FirstLine(ByVal raw As String) As String
    Dim s As String
    s = Replace(raw, vbCr, "")
    If InStr(s, vbLf) > 0 Then
        FirstLine = Trim$(Split(s, vbLf)(0))
    Else
        FirstLine = Trim$(s)
    End If
End Function
