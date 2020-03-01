#!/bin/sh
git diff --exit-code -- json > /dev/null||echo Unclean JSON folder
git diff --exit-code -- json > /dev/null||exit
echo Waiting for android device
adb wait-for-device
apkpath=$(adb shell pm path com.sega.PhantasyStarOnline2es | _py/_APK_package.py)
adb shell dumpsys package com.sega.PhantasyStarOnline2es| _py/_APK_version.py > /tmp/PSO2ver.txt
mkdir -p apk
echo pulling PSO2 APK
adb shell cp $apkpath /sdcard/PSO2es.zip
adb pull /sdcard/PSO2es.zip apk/PSO2es.zip
adb shell rm /sdcard/PSO2es.zip
echo Extracting DLLs
unzip -jo apk/PSO2es.zip -d apk
echo linking needed DLLs
ln -sf apk/Assembly-CSharp-firstpass.dll .
ln -sf apk/ContentsSerializer.dll .
ln -sf apk/ProtoBuffSerializer.dll .
ln -sf apk/protobuf-net.dll .
ln -sf apk/UnityEngine.dll .
mkdir -p Databases
rm -rf Databases/*
echo Getting stock Database files
adb pull -a /sdcard/Android/data/com.sega.PhantasyStarOnline2es/files/3hwQzp8KE9T1oTpJCHPvxI5JIedD3AuT/. Databases
echo Updating JSONs
mono ESBreakerCLI.exe > /dev/null
git commit --file /tmp/PSO2ver.txt -- json
# ./make.sh
