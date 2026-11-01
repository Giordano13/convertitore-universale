Option Explicit
Dim shell, fso, root
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = root
Function Quote(value)
    Quote = Chr(34) & value & Chr(34)
End Function
On Error Resume Next
If Not fso.FileExists(root & "\.venv\Scripts\pythonw.exe") Then
    MsgBox "Esegui prima Setup.vbs nella cartella estratta.", 48, "Convertitore Universale"
    WScript.Quit 1
End If
shell.Run Quote(root & "\.venv\Scripts\pythonw.exe") & " " & Quote(root & "\tools\launch_app.py"), 0, False
If Err.Number <> 0 Then
    MsgBox Err.Description, 16, "Convertitore Universale"
    WScript.Quit 1
End If
