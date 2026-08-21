@echo off
rem ============================================================
rem  OmniRouter - Windows launcher
rem  Starts the free-tier AI router on http://127.0.0.1:8787/v1
rem  Usage: omni-router.cmd   (or)   omni-router.cmd 8787
rem ============================================================
setlocal
if not "%~1"=="" set OMNI_PORT=%~1
if not defined OMNI_PORT set OMNI_PORT=8787

rem Locate python (python or py)
set PY=python
where py >nul 2>nul && set PY=py

echo [OmniRouter] Starting on port %OMNI_PORT% ...
%PY% "%~dp0..\omni_router\omni_router.py"
