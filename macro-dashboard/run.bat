@echo off
chcp 65001 >nul
title MACRO DASHBOARD
setlocal enabledelayedexpansion

set MVN=C:\Users\MILKYO~1\scoop\apps\maven\current\bin\mvn.cmd
set POM=%~dp0pom.xml

set MODE=run
if "%~1"=="test" set MODE=test
if "%~2"=="test" set MODE=test
if "%~1"=="--test" set MODE=test

if "%MODE%"=="test" (
    echo.
    echo  Running tests...
    echo.
    "%MVN%" -f "%POM%" test
    echo.
    echo  Done.
    pause
    exit /b 0
)

echo.
echo  [1/2] Building with Maven...
"%MVN%" -f "%POM%" clean package -DskipTests -q

if not !ERRORLEVEL!==0 (
    echo  [ERROR] Build FAILED
    pause
    exit /b 1
)
echo  [OK]
echo.

echo  [2/2] Running MACRO DASHBOARD
echo.
java -Dfile.encoding=UTF-8 "-Dsun.stdout.encoding=UTF-8" "-Dsun.stderr.encoding=UTF-8" -cp "%~dp0target\classes" com.tradingtabs.cli.Main --html

if exist "%~dp0dashboard.html" (
    echo.
    echo  HTML: dashboard.html
    start "" "%~dp0dashboard.html"
)
echo.
echo  Done.
pause
