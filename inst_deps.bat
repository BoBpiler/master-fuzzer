@echo off
copy csmith\m4.exe c:\windows\system32
copy csmith\regex2.dll c:\windows\system32

pip install progressbar
pip install requests
pip install psutil
pip install windows-curses

ssh-keygen -t rsa -b 4096 -f "%~dp0BoBpiler" -N "BoBpiler BoBpiler"
