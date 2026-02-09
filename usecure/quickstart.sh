#!/bin/bash
# Quick Start Script for UBL Fraud Detection System

echo "========================================"
echo "UBL Fraud Detection System - Quick Start"
echo "========================================"

# Step 1: Install dependencies
echo ""
echo "Step 1: Installing dependencies..."
pip install -r requirements.txt

# Step 2: Create directories
echo ""
echo "Step 2: Creating directories..."
mkdir -p rules output temp

# Step 3: Generate sample data
echo ""
echo "Step 3: Generating sample transaction data..."
python generate_sample_data.py

# Step 4: Start the server
echo ""
echo "Step 4: Starting FastAPI server..."
echo ""
echo "The server will start on http://localhost:8000"
echo "API Documentation available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py
