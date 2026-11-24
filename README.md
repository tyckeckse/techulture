# Techulture

Local-first culture and art digest with a small local server and a Windows scheduled refresh.

## Setup

```powershell
Set-Location "<path-to-techulture>"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

## Build now

```powershell
& .\.venv\Scripts\python.exe .\techulture.py
Start-Process .\index.html
```

## Serve locally

```powershell
& .\.venv\Scripts\python.exe .\app.py
```

Open `http://127.0.0.1:8021/`.

## Install & run all tasks

Recommended one-command setup: refresh task + server task.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\InstallAndRun-TechultureTasks.ps1
```

## Remove all tasks

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Remove-TechultureTasks.ps1
```

## Install & run refresh task

Defaults: task name `TechultureRefresh`, daily at `05:00`, `12:00`, and `18:00`, plus startup and logon. Mode `SilentVbs`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\InstallAndRun-TechultureRefreshTask.ps1
```

## Remove refresh task

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Remove-TechultureRefreshTask.ps1
```

## Install server task

Defaults: task name `TechultureServer`, startup + logon, URL `http://127.0.0.1:8021/`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\InstallAndRun-TechultureServerTask.ps1
```

## Remove server task

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Remove-TechultureServerTask.ps1
```

## Debug run with logs

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-TechultureRefresh.ps1
```

Logs are written to `.\logs\`.

## Published page

GitHub Actions (`.github/workflows/refresh.yml`) builds hourly, 04:17–21:17 UTC, and deploys to https://techulture.vercel.app.
Requires the repository secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`.

## Architecture

* techulture.py: the builder. It loads sources, fetches articles from the sites, normalizes them, saves data/store.json, then calls render_store_to_file(...) from render_index.py.
* render_index.py: the renderer. It takes the already-saved store and turns it into index.html.
* app.py: the web server. It serves the local files over http://127.0.0.1:8021/. It does not fetch or build anything.
* run_local.py: the convenience wrapper. It runs techulture.py first, then starts app.py.