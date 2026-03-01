@echo off
echo Starting Odoo 19 Documentation Crawler...
echo This will crawl all 2697 pages. Estimated time: 2-3 hours
echo.
cd /d "%~dp0"
python -m src.main crawl --urls urls.txt > crawl_log.txt 2>&1
echo.
echo Crawl completed!
echo Check crawl_log.txt for details
pause
