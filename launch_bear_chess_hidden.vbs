Option Explicit

Dim fso, shell, baseDir, exePath, batPath
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
exePath = baseDir & "\dist\BearChess\BearChess.exe"
batPath = baseDir & "\start_app.bat"

If fso.FileExists(exePath) Then
    shell.Run """" & exePath & """", 1, False
ElseIf fso.FileExists(batPath) Then
    shell.Run "cmd /c """ & batPath & """", 0, False
Else
    MsgBox "No launch target found. Please run start_app.bat or build_app.bat first.", 48, "Bear Chess"
End If
