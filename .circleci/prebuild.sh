#!/bin/bash -e
if [ -z "$1" ]
 then
	ProjectDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
 else
	ProjectDir="$( cd "$( dirname "$1/." )" && pwd )"
fi

UA="APK Ripper \(*NIX\)"

APKFilename=$(wget "http://pso2es.10nub.es/game.php?filename=true" --no-http-keep-alive --dns-timeout=15 --read-timeout=30 --user-agent "$UA" --quiet -O -)

Pathtolib="$ProjectDir/lib"
PathtoAPK="$Pathtolib/$APKFilename"

cd $Pathtolib

echo "Downloading $APKFilename from pso2es.10.nub.es to $ProjectDir"
wget "http://pso2es.10nub.es/game.php" --no-http-keep-alive --dns-timeout=15 --read-timeout=30 --user-agent "$UA" --quiet --continue --trust-server-names

echo "Deleting old APK files"
find . -name "*.apk" -not -name "$APKFilename" -delete

echo "Extracting DLLs from APK"
unzip -xujoq "$PathtoAPK" "assets/bin/Data/Managed/*.dll"
