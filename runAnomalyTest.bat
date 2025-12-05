@echo off
REM Anomaly Test Runner Script for Windows
REM Usage: run_anomaly_tests.bat [test_name]

setlocal enabledelayedexpansion

REM Configuration
set API_URL=http://localhost:8000
set PLOTS=1 2
set INTERVAL=60

echo ============================================
echo    Anomaly Test Runner (Windows)
echo ============================================
echo.

REM Get test name from argument or use default
set TEST_NAME=%1
if "%TEST_NAME%"=="" set TEST_NAME=quick_test

if "%TEST_NAME%"=="baseline" (
    echo Running Test: baseline
    echo Description: Baseline - No anomalies
    echo Duration: 2 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario baseline --duration 2
    goto :end
)

if "%TEST_NAME%"=="irrigation_failure" (
    echo Running Test: irrigation_failure
    echo Description: Sudden moisture drop
    echo Duration: 3 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario irrigation_failure --duration 3
    goto :end
)

if "%TEST_NAME%"=="1" (
    echo Running Test: irrigation_failure
    echo Description: Sudden moisture drop
    echo Duration: 3 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario irrigation_failure --duration 3
    goto :end
)

if "%TEST_NAME%"=="sensor_malfunction" (
    echo Running Test: sensor_malfunction
    echo Description: Random sensor spikes
    echo Duration: 2.5 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario sensor_malfunction --duration 2.5
    goto :end
)

if "%TEST_NAME%"=="2" (
    echo Running Test: sensor_malfunction
    echo Description: Random sensor spikes
    echo Duration: 2.5 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario sensor_malfunction --duration 2.5
    goto :end
)

if "%TEST_NAME%"=="calibration_drift" (
    echo Running Test: calibration_drift
    echo Description: Gradual sensor drift
    echo Duration: 5 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario calibration_drift --duration 5
    goto :end
)

if "%TEST_NAME%"=="3" (
    echo Running Test: calibration_drift
    echo Description: Gradual sensor drift
    echo Duration: 5 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario calibration_drift --duration 5
    goto :end
)

if "%TEST_NAME%"=="full_suite" (
    echo Running Test: full_suite
    echo Description: All anomalies in sequence
    echo Duration: 9 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario full_suite --duration 9
    goto :end
)

if "%TEST_NAME%"=="quick_test" (
    echo Running Test: quick_test
    echo Description: Quick validation test
    echo Duration: 2 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario quick_test --duration 2
    goto :end
)

if "%TEST_NAME%"=="quick" (
    echo Running Test: quick_test
    echo Description: Quick validation test
    echo Duration: 2 hours
    echo.
    python sensor_simulator_enhanced.py --api-url %API_URL% --plots %PLOTS% --interval %INTERVAL% --scenario quick_test --duration 2
    goto :end
)

if "%TEST_NAME%"=="help" goto :help
if "%TEST_NAME%"=="-h" goto :help
if "%TEST_NAME%"=="--help" goto :help

echo Error: Unknown test '%TEST_NAME%'
echo Run 'run_anomaly_tests.bat help' for usage information
goto :eof

:help
echo Usage: run_anomaly_tests.bat [test_name]
echo.
echo Available tests:
echo   baseline             - No anomalies (normal operation)
echo   irrigation_failure   - Sudden moisture drop (3 hours)
echo   sensor_malfunction   - Random sensor spikes (2.5 hours)
echo   calibration_drift    - Gradual sensor drift (5 hours)
echo   quick_test           - Quick validation (~2 hours)
echo   full_suite           - All anomalies in sequence (~9 hours)
echo.
echo Shortcuts:
echo   1 = irrigation_failure
echo   2 = sensor_malfunction
echo   3 = calibration_drift
echo.
echo Examples:
echo   run_anomaly_tests.bat quick_test
echo   run_anomaly_tests.bat 1
echo   run_anomaly_tests.bat full_suite
goto :eof

:end
echo.
echo ============================================
echo Test run completed
echo ============================================