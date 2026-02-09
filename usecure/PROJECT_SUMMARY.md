# UBL Fraud Detection System - Project Summary

## Overview
This is a complete FastAPI-based fraud detection system POC for United Bank Limited. The system analyzes historical transaction patterns to create adaptive fraud detection rules and applies them to real-time transactions.

## Project Structure

```
ubl_fraud_detection_api/
├── main.py                                      # FastAPI application with endpoints
├── fraud_rules_generator.py                     # Rules generation logic
├── fraud_detector.py                            # Fraud detection logic
├── config.py                                    # Configuration settings
├── requirements.txt                             # Python dependencies
├── generate_sample_data.py                      # Sample data generator
├── test_api.py                                  # API testing script
├── README.md                                    # Main documentation
├── USAGE_EXAMPLES.md                            # Detailed usage guide
├── quickstart.sh                                # Quick start script (Linux/Mac)
├── quickstart.bat                               # Quick start script (Windows)
└── UBL_Fraud_Detection_API.postman_collection.json  # Postman collection
```

## Key Features

### 1. Rules Generation (API Endpoint 1)
- **Input**: CSV file with 3+ months of transaction data + reference date
- **Process**: 
  - Analyzes last 3 months of DEBIT transactions before reference date
  - Creates account-specific behavioral profiles
  - Calculates percentiles using IQR method for adaptive thresholds
- **Output**: CSV file with rules for each account

### 2. Fraud Detection (API Endpoint 2)
- **Input**: CSV file with transactions + detection date + rules date
- **Process**:
  - Processes transactions chronologically
  - Calculates cumulative metrics in real-time
  - Applies 8 fraud detection rules
  - Scores each transaction
- **Output**: CSV file with all transactions and fraud flags

## Fraud Detection Rules

| Rule | Description | Score |
|------|-------------|-------|
| 1. Device Change | Device differs from historical frequent devices | 1 |
| 2. Daily Debit Count | Exceeds upper bound (≥3 txns) | 1 |
| 3. Daily Debit Amount | Exceeds upper bound | 1 |
| 4. Transaction Amount | Exceeds upper bound AND >200k | 1 |
| 5. Hourly Count | Exceeds upper bound (≥3 txns) | 1 |
| 6. New Beneficiary High Txn | Large amount to new beneficiary | 1 |
| 7. Unusual Hour | Transaction at unusual time (≥49,999) | 1 |
| 8. Device + New Bene + BB | Device change + new bene + microfinance ≥75k | 1 |

**Fraud Detected If**: Score ≥ 3 OR Rule 6 triggered

## Installation & Setup

### Quick Start
```bash
# Linux/Mac
chmod +x quickstart.sh
./quickstart.sh

# Windows
quickstart.bat
```

### Manual Setup
```bash
pip install -r requirements.txt
mkdir -p rules output temp
python generate_sample_data.py
python main.py
```

## API Endpoints

### 1. POST /api/v1/generate-rules
Generates fraud detection rules from historical data.

**Request**:
- `file`: CSV file (multipart/form-data)
- `input_date`: DD/MM/YYYY

**Response**: JSON with status and rules file info

### 2. POST /api/v1/detect-fraud
Detects fraud using pre-generated rules.

**Request**:
- `file`: CSV file (multipart/form-data)
- `detection_date`: DD/MM/YYYY
- `rules_date`: DD/MM/YYYY

**Response**: CSV file download with results

### 3. GET /api/v1/rules/list
Lists all available rules files.

**Response**: JSON with list of rules files

## Input Data Format

CSV with these columns:
```
account_number          # Account identifier
transaction_id          # Unique transaction ID
transaction_timestamp   # DD/MM/YYYY HH:MM:SS
transaction_amount      # Numeric amount
cr_dr_ind              # C (credit) or D (debit)
New Beneficiary Flag   # 0 (existing) or 1 (new)
device_id              # Device identifier
transaction_type_code  # Transaction type
```

## Output Data Format

Input columns PLUS:

**Real-time Features**:
- transaction_hour
- first_destination_new_logic
- device_id_current
- cumulative_daily_amount
- cumulative_daily_count
- cumulative_hourly_count
- transaction_value
- cumulative_microfinance_daily_amount

**Account Rules** (for reference):
- most_freq_devid_wkly
- most_freq_devid_1m
- daily_debit_txn_count_upper_bound
- daily_debit_amt_upper_bound
- daily_debit_amt_p50
- txn_amt_upper_bound
- hourly_debit_transaction_count_upper_bound

**Fraud Flags** (0/1):
- fraud_device_change
- fraud_daily_debit_count
- fraud_daily_debit_amt
- fraud_txn_amt
- fraud_hourly_count
- fraud_new_bene_high_transaction
- fraud_unusual_hour
- fraud_device_change_new_bene_bb_75k

**Final Detection**:
- rule_based_fraud_score (0-8)
- rule_based_fraud_detected (True/False)

## Configuration

Edit `config.py` to customize:

```python
# Microfinance transaction codes (configurable)
MICROFINANCE_TRANSACTION_CODES = ['ezpsa', 'jzzcsh', 'nypy']

# IQR multiplier for upper bounds
IQR_MULTIPLIER = 1.5

# Fraud detection thresholds
FRAUD_DETECTION_CONFIG = {
    'minimum_fraud_score': 3,
    'unusual_hour_amount_threshold': 49999,
    'high_transaction_amount_threshold': 200000,
    'minimum_daily_debit_count': 3,
    'minimum_hourly_count': 3,
    'device_change_microfinance_threshold': 75000
}
```

## Testing

### 1. Generate Sample Data
```bash
python generate_sample_data.py
```

### 2. Run Test Suite
```bash
python test_api.py
```

### 3. Manual Testing
```bash
# Test rules generation
curl -X POST "http://localhost:8000/api/v1/generate-rules" \
  -F "file=@sample_transactions.csv" \
  -F "input_date=31/12/2023"

# Test fraud detection
curl -X POST "http://localhost:8000/api/v1/detect-fraud" \
  -F "file=@sample_transactions.csv" \
  -F "detection_date=01/01/2024" \
  -F "rules_date=31/12/2023" \
  --output results.csv
```

## Important Notes

1. **DEBIT Transactions Only**: Rules and detection apply only to debit transactions
2. **Chronological Processing**: Transactions processed in time order for accurate cumulative metrics
3. **N-1 Rules**: Rules generated from data BEFORE the reference date
4. **Date Format**: Always use DD/MM/YYYY
5. **Timestamp Format**: DD/MM/YYYY HH:MM:SS
6. **CSV Storage**: Uses file-based storage (can be upgraded to database)

## File Descriptions

| File | Purpose |
|------|---------|
| main.py | FastAPI application with 3 endpoints |
| fraud_rules_generator.py | Generates account-level rules from historical data |
| fraud_detector.py | Applies rules to detect fraud in real-time |
| config.py | Configuration settings and thresholds |
| generate_sample_data.py | Creates sample transaction data for testing |
| test_api.py | Automated test suite for API endpoints |
| README.md | Main documentation |
| USAGE_EXAMPLES.md | Detailed usage examples and workflows |
| quickstart.sh | Quick start script for Linux/Mac |
| quickstart.bat | Quick start script for Windows |
| UBL_Fraud_Detection_API.postman_collection.json | Postman collection for API testing |
| requirements.txt | Python dependencies |

## Code Fixes Applied

The following issues from the original PySpark code were fixed:

1. **Rule 1**: Fixed missing closing parenthesis
2. **Rule 4**: Changed Python `and` to PySpark `&` operator
3. **Rule 7**: Added hour_0_pct (was missing, had hour_24_pct instead)
4. **All Rules**: Converted to pandas-compatible syntax

## Workflow Example

```
1. Upload historical data (3 months) → Generate Rules
   Input: transactions.csv (Oct-Dec 2023)
   Date: 31/12/2023
   Output: fraud_rules_20231231.csv

2. Upload transaction data → Detect Fraud
   Input: transactions.csv (Jan 2024)
   Detection Date: 01/01/2024
   Rules Date: 31/12/2023
   Output: fraud_detection_results_20240101_HHMMSS.csv

3. Analyze Results
   - Total transactions: X
   - Fraudulent: Y (Z%)
   - High-risk accounts: A
   - Amount at risk: $B
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Dependencies

- FastAPI 0.109.0
- uvicorn 0.27.0
- pandas 2.1.4
- numpy 1.26.3
- python-multipart 0.0.6

## Performance Considerations

- **Memory**: Entire datasets loaded in memory
- **Processing**: Sequential chronological processing
- **Storage**: CSV files (can be slow for large datasets)
- **Recommendation**: For production, consider:
  - Database storage (PostgreSQL)
  - Batch processing for large datasets
  - Caching frequently accessed rules

## Next Steps for Production

1. Database integration
2. User authentication
3. Rate limiting
4. Logging and monitoring
5. Email/SMS alerts for fraud
6. Dashboard for visualization
7. API versioning
8. Docker containerization
9. CI/CD pipeline
10. Load balancing

## Support

- API Documentation: http://localhost:8000/docs
- Test Script: `python test_api.py`
- Sample Data: `python generate_sample_data.py`

## Version

**Version**: 1.0.0  
**Date**: February 2026  
**Status**: POC Ready for Testing

---

**Note**: This is a proof-of-concept implementation. For production deployment, additional security, scalability, and monitoring features should be implemented.
