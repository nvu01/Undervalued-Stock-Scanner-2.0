@echo off

:task1
echo [TASK 1 of 2] File Processing for the Scanner
echo ========================================================================
echo Make sure to update the "Downloaded CSV Files" folder before continuing!
echo ========================================================================

choice /c YN /m "Press Y to continue, N to skip this task"

if errorlevel 2 (
    echo Task 1 skipped.
    goto task2
)

if errorlevel 1 (
    cd "D:\PROJECTS\Undervalued Stock Scanner V2"
    python -m SCRIPTS.etl
    echo --------------------------------------------------------------------------------------------
    echo File processing complete! Files in "Results" and "Industry Means" folders have been updated.
    echo Open "POWER BI\Undervalued Stock Scanner.pbix" to refresh data and see the scanned results.
    echo --------------------------------------------------------------------------------------------
)


:task2
echo.
echo.
echo.
echo [TASK 2 of 2] File Processing for Exit Signal Detection
echo =====================================================================================================
echo Before continuing, make sure to download a new position statement to the "Position Statement" folder!
echo =====================================================================================================

choice /c YN /m "Press Y to continue, N to cancel"

if errorlevel 2 (
    echo Cancelled.
    goto end
)

if errorlevel 1 (
    cd "D:\PROJECTS\Undervalued Stock Scanner V2"
    python -m SCRIPTS.exit_signals
    echo ------------------------------------------------------------------------------
    echo File processing complete! Files in "Exit Signals" folder have been updated.
    echo Open "POWER BI\Exit Signals.pbix" to refresh data and see the scanned results.
    echo ------------------------------------------------------------------------------
)


:end
pause