@echo off
copy src\csmith\m4.exe c:\windows\system32
copy src\csmith\regex2.dll c:\windows\system32

pip install progressbar
pip install requests

ssh-keygen -t rsa -b 4096 -f "%~dp0BoBpiler" -N "BoBpiler BoBpiler"