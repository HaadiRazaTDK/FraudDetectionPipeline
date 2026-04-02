"""
FastAPI Fraud Detection System for United Bank Limited
Supports CSV and Excel (.xlsx) file formats
Currency: PKR (Pakistani Rupees)
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict
import os
import logging
from pathlib import Path
from io import BytesIO

from fraud_rules_generator import FraudRulesGenerator
from fraud_detector import FraudDetector
from dashboard_generator import DashboardGenerator
from config import MICROFINANCE_TRANSACTION_CODES, RULES_DIR, OUTPUT_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Helper function to read both CSV and Excel files
def read_file(file_object) -> pd.DataFrame:
    """
    Read CSV or Excel file from upload
    
    Args:
        file_object: File-like object from FastAPI upload
        
    Returns:
        DataFrame with the file contents
    """
    # Read the file content
    content = file_object.read()
    file_object.seek(0)  # Reset position for potential re-reads
    
    try:
        # Try Excel first (.xlsx)
        df = pd.read_excel(BytesIO(content))
        logger.info("File read as Excel format")
        return df
    except Exception as excel_error:
        try:
            # Fall back to CSV
            df = pd.read_csv(BytesIO(content))
            logger.info("File read as CSV format")
            return df
        except Exception as csv_error:
            logger.error(f"Failed to read as Excel: {excel_error}, Failed to read as CSV: {csv_error}")
            raise ValueError("File must be in CSV or Excel (.xlsx) format")

# Create necessary directories
Path(RULES_DIR).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="UBL Fraud Detection System",
    description="Real-time fraud detection system for United Bank Limited",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "UBL Fraud Detection System API",
        "status": "active",
        "endpoints": {
            "generate_rules": "/api/v1/generate-rules",
            "detect_fraud": "/api/v1/detect-fraud"
        }
    }


@app.post("/api/v1/generate-rules")
async def generate_rules(
    file: UploadFile = File(..., description="Transaction data file (CSV or Excel .xlsx)"),
    input_date: str = Form(..., description="Reference date (DD/MM/YYYY) - rules will be generated from 3 months before this date")
):
    """
    Generate fraud detection rules for each account based on historical data.
    
    Args:
        file: CSV or Excel file with columns - account_number, transaction_id, transaction_timestamp,
              transaction_amount, cr_dr_ind, New Beneficiary Flag, device_id, transaction_type_code
        input_date: Reference date in DD/MM/YYYY format
        
    Returns:
        Success message with path to generated rules file
    """
    try:
        logger.info(f"Received rules generation request for date: {input_date}")
        
        # Validate date format
        try:
            reference_date = datetime.strptime(input_date, "%d/%m/%Y")
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid date format. Please use DD/MM/YYYY"
            )
        
        # Read uploaded file (CSV or Excel)
        try:
            df = read_file(file.file)
            logger.info(f"Loaded {len(df)} transactions from uploaded file")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Validate required columns
        required_columns = [
            'account_number', 'transaction_id', 'transaction_timestamp',
            'transaction_amount', 'cr_dr_ind', 'New Beneficiary Flag',
            'device_id', 'transaction_type_code'
        ]
        
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Generate rules
        generator = FraudRulesGenerator()
        rules_df = generator.generate_rules(df, reference_date)
        
        # Save rules to CSV
        rules_filename = f"fraud_rules_{reference_date.strftime('%Y%m%d')}.csv"
        rules_path = os.path.join(RULES_DIR, rules_filename)
        rules_df.to_csv(rules_path, index=False)
        
        logger.info(f"Rules generated successfully: {rules_path}")
        
        return {
            "status": "success",
            "message": "Fraud detection rules generated successfully",
            "reference_date": input_date,
            "rules_file": rules_filename,
            "accounts_processed": len(rules_df),
            "date_range": {
                "start": (reference_date - timedelta(days=90)).strftime("%d/%m/%Y"),
                "end": reference_date.strftime("%d/%m/%Y")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating rules: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating rules: {str(e)}")


@app.post("/api/v1/detect-fraud")
async def detect_fraud(
    file: UploadFile = File(..., description="Transaction data file (CSV or Excel .xlsx)"),
    detection_date: str = Form(..., description="Date to detect fraud (DD/MM/YYYY)"),
    rules_date: str = Form(..., description="Date of rules file to use (DD/MM/YYYY)")
):
    """
    Detect fraud in transactions for a specific date using pre-generated rules.
    
    Args:
        file: CSV or Excel file with transaction data
        detection_date: Date for which to detect fraud (DD/MM/YYYY)
        rules_date: Date of the rules file to use (DD/MM/YYYY)
        
    Returns:
        CSV file download with fraud detection results
    """
    try:
        logger.info(f"Received fraud detection request for date: {detection_date}")
        
        # Validate dates
        try:
            detect_dt = datetime.strptime(detection_date, "%d/%m/%Y")
            rules_dt = datetime.strptime(rules_date, "%d/%m/%Y")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Please use DD/MM/YYYY"
            )
        
        # Check if rules file exists
        rules_filename = f"fraud_rules_{rules_dt.strftime('%Y%m%d')}.csv"
        rules_path = os.path.join(RULES_DIR, rules_filename)
        
        if not os.path.exists(rules_path):
            raise HTTPException(
                status_code=404,
                detail=f"Rules file not found for date {rules_date}. Please generate rules first."
            )
        
        # Load rules
        rules_df = pd.read_csv(rules_path)
        logger.info(f"Loaded rules for {len(rules_df)} accounts")
        
        # Read transaction data (CSV or Excel)
        try:
            df = read_file(file.file)
            logger.info(f"Loaded {len(df)} transactions from uploaded file")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Validate required columns
        required_columns = [
            'account_number', 'transaction_id', 'transaction_timestamp',
            'transaction_amount', 'cr_dr_ind', 'New Beneficiary Flag',
            'device_id', 'transaction_type_code'
        ]
        
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Detect fraud
        detector = FraudDetector(rules_df)
        results_df = detector.detect_fraud(df, detect_dt)
        
        # Save results to CSV
        output_filename = f"fraud_detection_results_{detect_dt.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        results_df.to_csv(output_path, index=False)
        
        logger.info(f"Fraud detection completed. Results saved to: {output_path}")
        
        # Return CSV file for download
        return FileResponse(
            path=output_path,
            media_type='text/csv',
            filename=output_filename,
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting fraud: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error detecting fraud: {str(e)}")


@app.get("/api/v1/rules/list")
async def list_rules():
    """List all available rules files"""
    try:
        rules_files = [f for f in os.listdir(RULES_DIR) if f.endswith('.csv')]
        
        rules_info = []
        for filename in sorted(rules_files, reverse=True):
            file_path = os.path.join(RULES_DIR, filename)
            file_stats = os.stat(file_path)
            
            # Extract date from filename
            date_str = filename.replace('fraud_rules_', '').replace('.csv', '')
            try:
                file_date = datetime.strptime(date_str, '%Y%m%d')
                formatted_date = file_date.strftime('%d/%m/%Y')
            except:
                formatted_date = date_str
            
            rules_info.append({
                "filename": filename,
                "date": formatted_date,
                "size_kb": round(file_stats.st_size / 1024, 2),
                "created": datetime.fromtimestamp(file_stats.st_ctime).strftime('%d/%m/%Y %H:%M:%S')
            })
        
        return {
            "status": "success",
            "rules_files": rules_info,
            "total_files": len(rules_info)
        }
        
    except Exception as e:
        logger.error(f"Error listing rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing rules: {str(e)}")


@app.post("/api/v1/dashboard-metrics")
async def generate_dashboard_metrics(
    file: UploadFile = File(..., description="Fraud detection results file (CSV or Excel .xlsx)"),
):
    """
    Generate dashboard metrics from fraud detection results.
    
    This endpoint processes fraud detection output and generates comprehensive metrics
    for the fraud monitoring dashboard, including:
    - Executive summary (fraud count, percentage, total amount in PKR)
    - Key risk indicators (severity index, accounts requiring action)
    - Actionable alerts (prioritized accounts for action)
    - Fraud distribution analysis (by beneficiary type, transaction type)
    - Top affected accounts (concentration of risk)
    - Amount distribution (fraud by amount ranges in PKR)
    - Temporal analysis (patterns by hour/day)
    - Transaction details (high-risk transactions)
    
    Args:
        file: CSV or Excel file with fraud detection results (output from detect_fraud endpoint)
        
    Returns:
        JSON with comprehensive dashboard metrics organized by category (amounts in PKR)
    """
    try:
        logger.info("Received dashboard metrics generation request")
        
        # Read fraud detection results file (CSV or Excel)
        try:
            results_df = read_file(file.file)
            logger.info(f"Loaded {len(results_df)} records from fraud detection results")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Validate required columns
        required_columns = ['account_number', 'transaction_id', 'transaction_timestamp', 
                           'transaction_amount', 'rule_based_fraud_detected', 'rule_based_fraud_score']
        
        missing_columns = set(required_columns) - set(results_df.columns)
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in fraud detection results: {missing_columns}"
            )
        
        # Generate dashboard metrics
        generator = DashboardGenerator(results_df)
        dashboard_data = generator.generate_dashboard_data()
        
        logger.info("Dashboard metrics generated successfully")
        
        return {
            "status": "success",
            "message": "Dashboard metrics generated successfully (amounts in PKR)",
            "data": dashboard_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating dashboard metrics: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
