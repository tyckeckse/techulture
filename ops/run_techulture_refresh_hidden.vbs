Option Explicit

Dim shell, fso, scriptDir, projectRoot
Dim pythonwExe, pythonwArgs, buildScript, storePath, outPath, cmd
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

buildScript = fso.BuildPath(projectRoot, "techulture.py")
storePath = fso.BuildPath(projectRoot, "data\store.json")
outPath = fso.BuildPath(projectRoot, "index.html")

If Not fso.FileExists(buildScript) Then
    WScript.Quit 1
End If

cmd = """" & pythonwExe & """" & pythonwArgs & _
    " """ & buildScript & """" & _
    " --store """ & storePath & """" & _
    " --out """ & outPath & """"

' 0 = hidden window, False = do not wait for completion
shell.Run cmd, 0, False
