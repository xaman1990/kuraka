@echo off
REM kuraka.cmd — Windows shim for the Kuraka CLI. Dispatches to kuraka.py with the
REM available Python launcher (`py -3` preferred, else `python`). Put this file's
REM directory (the vault) on PATH via install.ps1 so `kuraka ...` works anywhere.
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0kuraka.py" %*
) else (
  python "%~dp0kuraka.py" %*
)
