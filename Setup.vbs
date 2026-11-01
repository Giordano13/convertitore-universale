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
shell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File " & Quote(root & "\tools\setup_source.ps1"), 0, False
If Err.Number <> 0 Then
    MsgBox Err.Description, 16, "Convertitore Universale"
    WScript.Quit 1
End If
