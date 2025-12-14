@echo off
echo === School Cafe Apps Script Deployment Script ===
echo.

echo 1. Checking clasp installation...
clasp --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: clasp is not installed. Run: npm install -g @google/clasp
    pause
    exit /b 1
)
echo ✓ clasp is installed

echo.
echo 2. Checking login status...
clasp login --status >nul 2>&1
if %errorlevel% neq 0 (
    echo Please login to clasp first:
    clasp login
    pause
    exit /b 1
)
echo ✓ Logged in to clasp

echo.
echo 3. Checking if project exists...
if not exist ".clasp.json" (
    echo Creating new Apps Script project...
    clasp create --title "School Cafe App" --type standalone
) else (
    echo ✓ Project configuration found
)

echo.
echo 4. Pushing code to Apps Script...
clasp push

echo.
echo 5. Opening Apps Script editor...
clasp open

echo.
echo === Deployment completed! ===
echo.
echo Next steps:
echo 1. In Apps Script editor: Enable Vision API and Docs API in Services
echo 2. Create a Google Sheet and copy its ID
echo 3. Update the spreadsheet ID in apps_script.gs
echo 4. Deploy as web app: Deploy → New deployment → Web app
echo 5. Copy the web app URL and test the application
echo.
pause