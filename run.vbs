Option Explicit

Dim fso, shell, scriptDir, py, pyw, cmd, exitCode

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

py = FindPythonExe()
If py = "" Then
  MsgBox "Python not found. Install Python 3.10 or later.", vbCritical, "CursorUsageTray"
  WScript.Quit 1
End If

pyw = PythonwFromPython(py)
If Not fso.FileExists(pyw) And LCase(py) <> "python" And LCase(py) <> "pythonw" Then
  MsgBox "pythonw.exe not found: " & pyw, vbCritical, "CursorUsageTray"
  WScript.Quit 1
End If

cmd = Quote(py) & " -m pip install -r requirements.txt -q"
exitCode = shell.Run(cmd, 0, True)
If exitCode <> 0 Then
  MsgBox "pip install failed, exit code: " & exitCode, vbCritical, "CursorUsageTray"
  WScript.Quit exitCode
End If

cmd = Quote(pyw) & " " & Quote(scriptDir & "\\main.py")
shell.Run cmd, 0, False

Function FindPythonExe()
  If fso.FileExists("C:\\Software\\Python313\\python.exe") Then
    FindPythonExe = "C:\\Software\\Python313\\python.exe"
    Exit Function
  End If
  If fso.FileExists("C:\\Software\\miniconda3\\python.exe") Then
    FindPythonExe = "C:\\Software\\miniconda3\\python.exe"
    Exit Function
  End If
  FindPythonExe = "python"
End Function

Function PythonwFromPython(pyExe)
  Dim lower, n
  lower = LCase(pyExe)
  n = Len(pyExe)
  If n >= 10 And Right(lower, 10) = "python.exe" Then
    PythonwFromPython = Left(pyExe, n - 10) & "pythonw.exe"
  ElseIf lower = "python" Or lower = "python3" Then
    PythonwFromPython = "pythonw"
  Else
    PythonwFromPython = pyExe
  End If
End Function

Function Quote(s)
  Quote = Chr(34) & s & Chr(34)
End Function
