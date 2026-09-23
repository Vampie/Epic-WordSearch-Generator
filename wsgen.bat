@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wsgen.ps1" %*
