# UBL Fraud Detection System - POC Backend

A FastAPI-based fraud detection system for United Bank Limited that analyzes transaction patterns and detects fraudulent activities in real-time.

## Overview

This system consists of two main components:

1. **Rules Generation**: Analyzes 3 months of historical transaction data to create account-specific behavioral rules
2. **Fraud Detection**: Applies these rules to real-time transactions to detect fraudulent activities

## Features

- **Adaptive Rule Generation**: Creates personalized fraud detection rules for each account based on historical behavior
- **Real-time Processing**: Processes transactions chronologically with cumulative tracking
- **Multi-layered Detection**: Uses 8 different fraud detection rules with weighted scoring
- **Configurable Thresholds**: Easy configuration of microfinance codes and fraud thresholds
- **CSV-based Storage**: Simple file-based storage for rules and results

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download the project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create necessary directories** (automatic on first run):
```bash
mkdir -p rules output temp
```

## Project Structure

```
.
├── main.py                      # FastAPI application and endpoints
├── fraud_rules_generator.py     # Rules generation logic
├── fraud_detector.py            # Fraud detection logic
├── config.py                    # Configuration settings
├── generate_sample_data.py      # Sample data generator for testing
├── requirements.txt             # Python dependencies
├── rules/                       # Generated rules files (CSV)
├── output/                      # Fraud detection results (CSV)
└── temp/                        # Temporary files
```

## Running the Application

### Start the API Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

API Documentation (Swagger UI): `http://localhost:8000/docs`

## API Endpoints

### 1. Generate Rules

**Endpoint**: `POST /api/v1/generate-rules`

**Description**: Generates fraud detection rules from historical transaction data (3 months before the input date).

**Parameters**:
- `file` (file): CSV file with transaction data
- `input_date` (form): Reference date in DD/MM/YYYY format

**Input CSV Format**:
```csv
account_number,transaction_id,transaction_timestamp,transaction_amount,cr_dr_ind,New Beneficiary Flag,device_id,transaction_type_code
ACC000001,TXN0000000001,01/01/2024 10:30:45,15000.00,D,0,DEV0001,transfer
ACC000001,TXN0000000002,01/01/2024 14:22:10,25000.00,D,1,DEV0001,ezpsa
```

**Response**:
```json
{
  "status": "success",
  "message": "Fraud detection rules generated successfully",
  "reference_date": "31/12/2023",
  "rules_file": "fraud_rules_20231231.csv",
  "accounts_processed": 100,
  "date_range": {
    "start": "02/10/2023",
    "end": "31/12/2023"
  }
}
```

**Generated Rules Include**:
- `most_freq_devid_wkly`: Most frequent device in last 7 days
- `most_freq_devid_1m`: Most frequent device in last 30 days
- Daily debit transaction count percentiles (p25, p50, p75, p90, upper_bound)
- Daily debit amount percentiles (p25, p50, p75, p90, upper_bound)
- Transaction amount percentiles (p25, p50, p75, p90, upper_bound)
- Hourly transaction count percentiles (p25, p50, p75, p90, upper_bound)
- Hour-wise transaction percentages (hour_0_pct to hour_23_pct)

### 2. Detect Fraud

**Endpoint**: `POST /api/v1/detect-fraud`

**Description**: Detects fraud in transactions for a specific date using pre-generated rules.

**Parameters**:
- `file` (file): CSV file with transaction data
- `detection_date` (form): Date to analyze in DD/MM/YYYY format
- `rules_date` (form): Date of the rules file to use in DD/MM/YYYY format

**Response**: CSV file download with fraud detection results

**Output CSV Columns**:

*Original Transaction Data*:
- account_number
- transaction_id
- transaction_timestamp
- transaction_amount
- cr_dr_ind
- New Beneficiary Flag
- device_id
- transaction_type_code

*Real-time Calculated Features*:
- transaction_hour
- first_destination_new_logic
- device_id_current
- cumulative_daily_amount
- cumulative_daily_count
- cumulative_hourly_count
- transaction_value
- cumulative_microfinance_daily_amount

*Account Rules (for reference)*:
- most_freq_devid_wkly
- most_freq_devid_1m
- daily_debit_txn_count_upper_bound
- daily_debit_amt_upper_bound
- daily_debit_amt_p50
- txn_amt_upper_bound
- hourly_debit_transaction_count_upper_bound

*Fraud Rule Flags (0/1)*:
- fraud_device_change
- fraud_daily_debit_count
- fraud_daily_debit_amt
- fraud_txn_amt
- fraud_hourly_count
- fraud_new_bene_high_transaction
- fraud_unusual_hour
- fraud_device_change_new_bene_bb_75k

*Final Detection*:
- rule_based_fraud_score (sum of all rule flags)
- rule_based_fraud_detected (True/False - fraud if score >= 3 OR fraud_new_bene_high_transaction)

### 3. List Available Rules

**Endpoint**: `GET /api/v1/rules/list`

**Description**: Lists all available rules files.

**Response**:
```json
{
  "status": "success",
  "rules_files": [
    {
      "filename": "fraud_rules_20231231.csv",
      "date": "31/12/2023",
      "size_kb": 245.6,
      "created": "15/01/2024 10:30:00"
    }
  ],
  "total_files": 1
}
```

## Fraud Detection Rules

The system applies 8 fraud detection rules:

### Rule 1: Device ID Change Detection
**Trigger**: Current device differs from most frequent device (weekly or monthly)
**Score**: 1 point

### Rule 2: Daily Debit Count Exceeds Upper Bound
**Trigger**: Cumulative daily count > upper_bound AND >= 3 transactions
**Score**: 1 point

### Rule 3: Daily Debit Amount Exceeds Upper Bound
**Trigger**: Cumulative daily amount > upper_bound
**Score**: 1 point

### Rule 4: Transaction Amount Exceeds Upper Bound
**Trigger**: Transaction > upper_bound AND > 200,000
**Score**: 1 point

### Rule 5: Hourly Transaction Count Exceeds Upper Bound
**Trigger**: Cumulative hourly count > upper_bound AND >= 3 transactions
**Score**: 1 point

### Rule 6: New Beneficiary with High Transaction Amount
**Trigger**: Transaction > daily_debit_amt_p50 AND first_destination = 1
**Score**: 1 point
**Special**: Also triggers fraud detection independently

### Rule 7: Unusual Hour Detection
**Trigger**: Transaction >= 49,999 in an hour with 0% historical activity
**Score**: 1 point

### Rule 8: Device Change + New Beneficiary + High Microfinance
**Trigger**: Device changed + new beneficiary + cumulative microfinance >= 75,000
**Score**: 1 point

### Final Fraud Detection
**Fraud Detected If**:
- Total score >= 3, OR
- Rule 6 (New Beneficiary High Transaction) is triggered

## Configuration

Edit `config.py` to customize:

```python
# Microfinance transaction codes
MICROFINANCE_TRANSACTION_CODES = ['ezpsa', 'jzzcsh', 'nypy']

# IQR multiplier for upper bound calculation
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

## Testing with Sample Data

Generate sample transaction data for testing:

```bash
python generate_sample_data.py
```

This creates `sample_transactions.csv` with:
- 50 accounts
- 120 days of transaction history
- Mix of normal and fraudulent transactions

## Usage Example

### Step 1: Generate Rules

```bash
curl -X POST "http://localhost:8000/api/v1/generate-rules" \
  -F "file=@sample_transactions.csv" \
  -F "input_date=31/12/2023"
```

### Step 2: Detect Fraud

```bash
curl -X POST "http://localhost:8000/api/v1/detect-fraud" \
  -F "file=@sample_transactions.csv" \
  -F "detection_date=01/01/2024" \
  -F "rules_date=31/12/2023" \
  --output fraud_results.csv
```

## Important Notes

1. **Only Debit Transactions**: All rules are calculated and applied only on DEBIT transactions (cr_dr_ind = 'D')

2. **Chronological Processing**: Transactions are processed in chronological order to calculate cumulative features accurately

3. **N-1 Rules**: Rules are generated from data up to (but not including) the reference date, representing N-1 day rules

4. **Date Format**: All dates must be in DD/MM/YYYY format

5. **Timestamp Format**: Transaction timestamps must be in DD/MM/YYYY HH:MM:SS format

6. **Missing Accounts**: If an account has no historical rules, default permissive values are used (high upper bounds)

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Rules file not found
- `500`: Server error

## Performance Considerations

- **Large Datasets**: For very large datasets (millions of transactions), consider processing in batches
- **Memory Usage**: The system loads entire datasets into memory - ensure adequate RAM
- **CSV Storage**: For production, consider migrating to a database for better performance

## Future Enhancements

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Real-time streaming support (Kafka/RabbitMQ)
- [ ] ML-based fraud scoring
- [ ] Dashboard for monitoring
- [ ] Alert notifications
- [ ] Multi-factor authentication
- [ ] API rate limiting

## Support

For issues or questions, please refer to the API documentation at `/docs` or contact the development team.

## License

Proprietary - United Bank Limited

---

**Version**: 1.0.0  
**Last Updated**: February 2026
