# UBL Fraud Detection System - Usage Examples

This document provides detailed examples of how to use the fraud detection system.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Workflow Overview](#workflow-overview)
3. [Example 1: Basic Usage](#example-1-basic-usage)
4. [Example 2: Multiple Dates Analysis](#example-2-multiple-dates-analysis)
5. [Example 3: Using Real Data](#example-3-using-real-data)
6. [Understanding Results](#understanding-results)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Option 1: Using Quick Start Script

**Linux/Mac**:
```bash
chmod +x quickstart.sh
./quickstart.sh
```

**Windows**:
```cmd
quickstart.bat
```

### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p rules output temp

# Generate sample data
python generate_sample_data.py

# Start server
python main.py
```

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW DIAGRAM                          │
└─────────────────────────────────────────────────────────────┘

Step 1: Prepare Historical Data (3+ months)
    ↓
    CSV File: transactions.csv
    
Step 2: Generate Rules
    ↓
    POST /api/v1/generate-rules
    - Upload: transactions.csv
    - Input Date: 31/12/2023
    ↓
    Output: fraud_rules_20231231.csv
    
Step 3: Detect Fraud
    ↓
    POST /api/v1/detect-fraud
    - Upload: transactions.csv (or new data)
    - Detection Date: 01/01/2024
    - Rules Date: 31/12/2023
    ↓
    Output: fraud_detection_results_20240101_HHMMSS.csv
    
Step 4: Analyze Results
    ↓
    Review flagged transactions
    Investigate fraud patterns
```

---

## Example 1: Basic Usage

### Step 1: Generate Sample Data

```bash
python generate_sample_data.py
```

This creates `sample_transactions.csv` with:
- 50 accounts
- 120 days of history (starting from 01/10/2023)
- Normal and fraudulent transactions

### Step 2: Generate Rules

**Using cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/generate-rules" \
  -F "file=@sample_transactions.csv" \
  -F "input_date=31/12/2023"
```

**Using Python**:
```python
import requests

url = "http://localhost:8000/api/v1/generate-rules"

with open("sample_transactions.csv", "rb") as f:
    files = {"file": f}
    data = {"input_date": "31/12/2023"}
    response = requests.post(url, files=files, data=data)

print(response.json())
```

**Expected Response**:
```json
{
  "status": "success",
  "message": "Fraud detection rules generated successfully",
  "reference_date": "31/12/2023",
  "rules_file": "fraud_rules_20231231.csv",
  "accounts_processed": 50,
  "date_range": {
    "start": "02/10/2023",
    "end": "31/12/2023"
  }
}
```

### Step 3: Detect Fraud

**Using cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/detect-fraud" \
  -F "file=@sample_transactions.csv" \
  -F "detection_date=01/01/2024" \
  -F "rules_date=31/12/2023" \
  --output fraud_results.csv
```

**Using Python**:
```python
import requests

url = "http://localhost:8000/api/v1/detect-fraud"

with open("sample_transactions.csv", "rb") as f:
    files = {"file": f}
    data = {
        "detection_date": "01/01/2024",
        "rules_date": "31/12/2023"
    }
    response = requests.post(url, files=files, data=data)

# Save results
with open("fraud_results.csv", "wb") as f:
    f.write(response.content)

print("Results saved to fraud_results.csv")
```

### Step 4: Analyze Results

```python
import pandas as pd

# Load results
df = pd.read_csv("fraud_results.csv")

# Basic statistics
print(f"Total Transactions: {len(df)}")
print(f"Fraudulent Transactions: {df['rule_based_fraud_detected'].sum()}")
print(f"Fraud Rate: {df['rule_based_fraud_detected'].mean() * 100:.2f}%")

# View fraudulent transactions
fraud_df = df[df['rule_based_fraud_detected'] == True]
print("\nFraudulent Transactions:")
print(fraud_df[['transaction_id', 'account_number', 'transaction_amount', 
                'rule_based_fraud_score']].head())

# Rule breakdown
rule_columns = [col for col in df.columns if col.startswith('fraud_')]
for col in rule_columns:
    if col != 'rule_based_fraud_detected':
        print(f"{col}: {df[col].sum()}")
```

---

## Example 2: Multiple Dates Analysis

Analyze fraud trends over multiple days:

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

base_url = "http://localhost:8000"

# Generate rules for December 31, 2023
with open("sample_transactions.csv", "rb") as f:
    response = requests.post(
        f"{base_url}/api/v1/generate-rules",
        files={"file": f},
        data={"input_date": "31/12/2023"}
    )
    print("Rules generated:", response.json())

# Detect fraud for first week of January
start_date = datetime(2024, 1, 1)
results = []

for day in range(7):
    detection_date = start_date + timedelta(days=day)
    date_str = detection_date.strftime("%d/%m/%Y")
    
    print(f"\nAnalyzing {date_str}...")
    
    with open("sample_transactions.csv", "rb") as f:
        response = requests.post(
            f"{base_url}/api/v1/detect-fraud",
            files={"file": f},
            data={
                "detection_date": date_str,
                "rules_date": "31/12/2023"
            }
        )
    
    if response.status_code == 200:
        # Save results
        output_file = f"fraud_results_{detection_date.strftime('%Y%m%d')}.csv"
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        # Analyze
        df = pd.read_csv(output_file)
        results.append({
            'date': date_str,
            'total_txns': len(df),
            'fraud_count': df['rule_based_fraud_detected'].sum(),
            'fraud_rate': df['rule_based_fraud_detected'].mean() * 100
        })

# Summary report
summary_df = pd.DataFrame(results)
print("\n=== Weekly Fraud Summary ===")
print(summary_df)
print(f"\nAverage Fraud Rate: {summary_df['fraud_rate'].mean():.2f}%")
```

---

## Example 3: Using Real Data

### Data Preparation

Your CSV file must have these columns:
```csv
account_number,transaction_id,transaction_timestamp,transaction_amount,cr_dr_ind,New Beneficiary Flag,device_id,transaction_type_code
```

**Example**:
```csv
account_number,transaction_id,transaction_timestamp,transaction_amount,cr_dr_ind,New Beneficiary Flag,device_id,transaction_type_code
1234567890,TXN001,01/01/2024 10:30:45,15000.00,D,0,DEVICE001,transfer
1234567890,TXN002,01/01/2024 14:22:10,25000.00,D,1,DEVICE001,ezpsa
1234567891,TXN003,01/01/2024 09:15:30,5000.00,C,0,DEVICE045,deposit
```

### Full Workflow

```python
import requests
import pandas as pd
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Step 1: Load your real data
print("Loading transaction data...")
df = pd.read_csv("your_transactions.csv")
print(f"Loaded {len(df)} transactions")

# Step 2: Determine dates
# Rules generation date (end of historical period)
rules_date = "31/12/2023"

# Detection dates (periods to analyze)
detection_dates = ["01/01/2024", "02/01/2024", "03/01/2024"]

# Step 3: Generate rules
print(f"\nGenerating rules for {rules_date}...")
with open("your_transactions.csv", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/generate-rules",
        files={"file": f},
        data={"input_date": rules_date}
    )

if response.status_code == 200:
    result = response.json()
    print(f"✓ Rules generated for {result['accounts_processed']} accounts")
    print(f"  Rules file: {result['rules_file']}")
else:
    print(f"✗ Error: {response.text}")
    exit(1)

# Step 4: Detect fraud for each date
for detection_date in detection_dates:
    print(f"\nDetecting fraud for {detection_date}...")
    
    with open("your_transactions.csv", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/v1/detect-fraud",
            files={"file": f},
            data={
                "detection_date": detection_date,
                "rules_date": rules_date
            }
        )
    
    if response.status_code == 200:
        output_file = f"fraud_results_{detection_date.replace('/', '')}.csv"
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        # Quick analysis
        results_df = pd.read_csv(output_file)
        fraud_count = results_df['rule_based_fraud_detected'].sum()
        total = len(results_df)
        
        print(f"✓ Results saved to {output_file}")
        print(f"  Analyzed: {total} transactions")
        print(f"  Fraud detected: {fraud_count} ({fraud_count/total*100:.2f}%)")
    else:
        print(f"✗ Error: {response.text}")

print("\n=== Analysis Complete ===")
```

---

## Understanding Results

### Output CSV Structure

The fraud detection results CSV contains:

#### 1. Original Transaction Data
- `account_number`: Account identifier
- `transaction_id`: Unique transaction ID
- `transaction_timestamp`: When transaction occurred
- `transaction_amount`: Transaction amount
- `cr_dr_ind`: Credit (C) or Debit (D)
- `New Beneficiary Flag`: 0 = existing, 1 = new
- `device_id`: Device used
- `transaction_type_code`: Type of transaction

#### 2. Real-time Calculated Features
- `transaction_hour`: Hour of transaction (0-23)
- `first_destination_new_logic`: New beneficiary indicator
- `device_id_current`: Current device ID
- `cumulative_daily_amount`: Total amount for the day so far
- `cumulative_daily_count`: Total transactions for the day so far
- `cumulative_hourly_count`: Transactions in current hour
- `transaction_value`: Transaction amount
- `cumulative_microfinance_daily_amount`: Total microfinance amount

#### 3. Account Rules (Reference)
- `most_freq_devid_wkly`: Most used device (last 7 days)
- `most_freq_devid_1m`: Most used device (last 30 days)
- `daily_debit_txn_count_upper_bound`: Max expected daily transactions
- `daily_debit_amt_upper_bound`: Max expected daily amount
- `daily_debit_amt_p50`: Median daily amount
- `txn_amt_upper_bound`: Max expected transaction amount
- `hourly_debit_transaction_count_upper_bound`: Max hourly transactions

#### 4. Fraud Rule Flags (0 or 1)
- `fraud_device_change`: Device differs from usual
- `fraud_daily_debit_count`: Too many transactions today
- `fraud_daily_debit_amt`: Total amount too high today
- `fraud_txn_amt`: Single transaction too large
- `fraud_hourly_count`: Too many transactions this hour
- `fraud_new_bene_high_transaction`: Large amount to new beneficiary
- `fraud_unusual_hour`: Transaction at unusual time
- `fraud_device_change_new_bene_bb_75k`: Multiple red flags

#### 5. Final Detection
- `rule_based_fraud_score`: Total points (sum of all flags)
- `rule_based_fraud_detected`: TRUE if fraud detected

### Interpreting Fraud Scores

| Score | Risk Level | Action |
|-------|-----------|--------|
| 0-2   | Low       | Normal transaction |
| 3-4   | Medium    | Review recommended |
| 5-6   | High      | Immediate review |
| 7+    | Critical  | Block and investigate |

### Example Analysis

```python
import pandas as pd

df = pd.read_csv("fraud_results.csv")

# High-risk accounts
high_risk = df[df['rule_based_fraud_score'] >= 5]
print(f"High-risk accounts: {high_risk['account_number'].nunique()}")

# Most common fraud patterns
fraud_df = df[df['rule_based_fraud_detected'] == True]

print("\nMost Triggered Rules:")
rules = [
    'fraud_device_change',
    'fraud_daily_debit_count',
    'fraud_daily_debit_amt',
    'fraud_txn_amt',
    'fraud_hourly_count',
    'fraud_new_bene_high_transaction',
    'fraud_unusual_hour',
    'fraud_device_change_new_bene_bb_75k'
]

for rule in rules:
    count = fraud_df[rule].sum()
    pct = count / len(fraud_df) * 100 if len(fraud_df) > 0 else 0
    print(f"  {rule}: {count} ({pct:.1f}%)")

# Amount at risk
total_fraud_amount = fraud_df['transaction_amount'].sum()
print(f"\nTotal amount in fraudulent transactions: {total_fraud_amount:,.2f}")
```

---

## Troubleshooting

### Common Issues

#### 1. Server Not Starting

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
python main.py --port 8001
```

#### 2. Rules File Not Found

**Error**: `Rules file not found for date XX/XX/XXXX`

**Solution**:
```bash
# List available rules
curl http://localhost:8000/api/v1/rules/list

# Generate rules for the required date
curl -X POST "http://localhost:8000/api/v1/generate-rules" \
  -F "file=@transactions.csv" \
  -F "input_date=XX/XX/XXXX"
```

#### 3. Invalid Date Format

**Error**: `Invalid date format`

**Solution**: Always use DD/MM/YYYY format
- Correct: `31/12/2023`
- Wrong: `2023-12-31`, `12/31/2023`

#### 4. Missing Columns

**Error**: `Missing required columns`

**Solution**: Ensure CSV has all required columns:
```python
required = [
    'account_number',
    'transaction_id',
    'transaction_timestamp',
    'transaction_amount',
    'cr_dr_ind',
    'New Beneficiary Flag',
    'device_id',
    'transaction_type_code'
]

df = pd.read_csv("your_file.csv")
missing = set(required) - set(df.columns)
if missing:
    print(f"Missing columns: {missing}")
```

#### 5. Memory Issues with Large Files

**Solution**: Process in batches
```python
# Split large file into chunks
chunk_size = 100000
for i, chunk in enumerate(pd.read_csv("large_file.csv", chunksize=chunk_size)):
    chunk.to_csv(f"chunk_{i}.csv", index=False)
    # Process each chunk separately
```

---

## Advanced Usage

### Custom Configuration

Edit `config.py` to customize:

```python
# Microfinance codes
MICROFINANCE_TRANSACTION_CODES = ['ezpsa', 'jzzcsh', 'nypy', 'custom1']

# Detection thresholds
FRAUD_DETECTION_CONFIG = {
    'minimum_fraud_score': 3,  # Lower for stricter detection
    'unusual_hour_amount_threshold': 30000,  # Adjust for your use case
    'high_transaction_amount_threshold': 150000,
    'minimum_daily_debit_count': 2,
    'minimum_hourly_count': 2,
    'device_change_microfinance_threshold': 50000
}
```

### Automated Daily Processing

```python
# daily_fraud_check.py
import requests
from datetime import datetime, timedelta
import schedule
import time

def daily_fraud_check():
    today = datetime.now().strftime("%d/%m/%Y")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    
    print(f"Running fraud detection for {today}...")
    
    # Detect fraud using yesterday's rules
    with open("daily_transactions.csv", "rb") as f:
        response = requests.post(
            "http://localhost:8000/api/v1/detect-fraud",
            files={"file": f},
            data={
                "detection_date": today,
                "rules_date": yesterday
            }
        )
    
    if response.status_code == 200:
        with open(f"fraud_results_{today.replace('/', '')}.csv", "wb") as f:
            f.write(response.content)
        print("✓ Fraud detection complete")
    else:
        print(f"✗ Error: {response.text}")

# Run daily at 2 AM
schedule.every().day.at("02:00").do(daily_fraud_check)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Support

For additional help:
1. Check API documentation at `http://localhost:8000/docs`
2. Review server logs for detailed error messages
3. Contact the development team

---

**Last Updated**: February 2026
