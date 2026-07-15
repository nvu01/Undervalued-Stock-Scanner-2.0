@echo off

echo ===========================================================================
echo Before continuing:
echo [] Update CSV files in "Downloaded CSV Files" folder
echo [] Download the position statement of the current month to "Position Statement" folder
echo ===========================================================================

choice /c YN /m "Press Y to continue, N to cancel"

if errorlevel 2 (
    echo Cancelled.
    goto end
)

if errorlevel 1 (
    cd /d "D:\PROJECTS\Undervalued Stock Scanner V2\SCRIPTS"
    set PYTHONPATH=D:\PROJECTS\Undervalued Stock Scanner V2
    python stock_database.py
    echo --------------------------------------------------------------------------------------------
    echo Stock data updated!
    echo Output: my_database.db and stock_data.csv
    echo To see the database, go to sqliteviewer.app and upload my_database.db in the project folder.
    echo --------------------------------------------------------------------------------------------
)

:end
pause