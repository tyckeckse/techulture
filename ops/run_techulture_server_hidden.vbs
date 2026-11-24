Option Explicit

Dim shell, fso, scriptDir, projectRoot
Dim pythonwExe, pythonwArgs, appScript, cmd
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptDir)
shell.CurrentDirectory = projectRoot

pythonwExe = fso.BuildPath(projectRoot, ".venv\Scripts\pythonw.exe")
pythonwArgs = ""
If Not fso.FileExists(pythonwExe) Then
    pythonwExe = "pyw.exe"
    pythonwArgs = " -3"
End If

appScript = fso.BuildPath(projectRoot, "app.py")
If Not fso.FileExists(appScript) Then
    WScript.Quit 1
End If

cmd = """" & pythonwExe & """" & pythonwArgs & _
    " """ & appScript & """" & _
    " --host 127.0.0.1 --port 8021"

' 0 = hidden window, True = wait so Task Scheduler keeps one running instance
shell.Run cmd, 0, True
