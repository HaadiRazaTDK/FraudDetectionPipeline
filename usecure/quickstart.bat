@echo off
REM Quick Start Script for UBL Fraud Detection System (Windows)

echo ========================================
echo UBL Fraud Detection System - Quick Start
echo ========================================

REM Step 1: Install dependencies
echo.
echo Step 1: Installing dependencies...
pip install -r requirements.txt

REM Step 2: Create directories
echo.
echo Step 2: Creating directories...
if not exist "rules" mkdir rules
if not exist "output" mkdir output
if not exist "temp" mkdir temp

REM Step 3: Generate sample data
echo.
echo Step 3: Generating sample transaction data...
python generate_sample_data.py

REM Step 4: Start the server
echo.
echo Step 4: Starting FastAPI server...
echo.
echo The server will start on http://localhost:8000
echo API Documentation available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py
