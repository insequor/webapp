@echo off
COLOR B

cmd /k "cd /d %~dp0\.env\Scripts & activate & cd /d    %~dp0 & python -m oktest test