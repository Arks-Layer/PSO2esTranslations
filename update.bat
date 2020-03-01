@echo off
git diff --exit-code -- json 1> nul||echo Unclean JSON folder
git diff --exit-code -- json 1> nul||pause&&exit
echo Waiting for android device
adb wait-for-device
adb shell pm path com.sega.PhantasyStarOnline2es | python _py\_APK_package.py > %TMP%\PSO2Path.txt && set /P apkpath=<%TMP%\PSO2Path.txt
adb shell dumpsys package com.sega.PhantasyStarOnline2es | python _py\_APK_version.py > %TMP%\PSO2ver.txt
mkdir apk 2> nul
echo pulling PSO2 APK
adb shell cp %apkpath% /sdcard/PSO2es.zip
adb pull /sdcard/PSO2es.zip apk\PSO2es.zip
adb shell rm /sdcard/PSO2es.zip
echo Extracting DLLs
Powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File unzip.ps1
echo linking needed DLLs
del /F /Q Assembly-CSharp-firstpass.dll && copy /B /V /Y /Z apk\Assembly-CSharp-firstpass.dll . 1> nul
del /F /Q ContentsSerializer.dll && copy /B /V /Y /Z apk\ContentsSerializer.dll ContentsSerializer.dll 1> nul
del /F /Q ProtoBuffSerializer.dll && copy /B /V /Y /Z apk\ProtoBuffSerializer.dll ProtoBuffSerializer.dll 1> nul
del /F /Q protobuf-net.dll && copy /B /V /Y /Z apk\protobuf-net.dll protobuf-net.dll 1> nul
del /F /Q UnityEngine.dll && copy /B /V /Y /Z apk\UnityEngine.dll UnityEngine.dll 1> nul
mkdir Databases 2> nul
del /Q /S Databases
echo Getting stock Database files
adb pull -a /sdcard/Android/data/com.sega.PhantasyStarOnline2es/files/3hwQzp8KE9T1oTpJCHPvxI5JIedD3AuT/. Databases
echo Updating JSONs
ESBreakerCLI.exe 1> nul
git commit --file %TMP%\PSO2ver.txt -- json 2> nul
rem call make.bat
