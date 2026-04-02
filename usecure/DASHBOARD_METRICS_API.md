# Dashboard Metrics Endpoint Documentation

## Overview
The **Dashboard Metrics** endpoint processes fraud detection results and generates comprehensive metrics for visualization on the fraud monitoring dashboard. It's designed specifically for the fraud monitoring unit to quickly understand fraud patterns and prioritize responses.

**Currency:** PKR (Pakistani Rupees - ₨)  
**File Formats Supported:** CSV and Excel (.xlsx)

## Endpoint Details

### URL
```
POST /api/v1/dashboard-metrics
```

### Request
**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): CSV or Excel file with fraud detection results (output from `/api/v1/detect-fraud` endpoint)

### Response
Returns JSON with status and comprehensive dashboard metrics organized by category (all monetary amounts in PKR).

## Response Structure

```json
{
  "status": "success",
  "message": "Dashboard metrics generated successfully (amounts in PKR)",
  "data": {
    "summary": { ... },
    "key_indicators": { ... },
    "actionable_alerts": { ... },
    "fraud_distribution": { ... },
    "top_accounts": { ... },
    "amount_distribution": { ... },
    "temporal_analysis": { ... },
    "transaction_details": { ... },
    "metadata": { ... }
  }
}
```

## Detailed Response Fields

### 1. Summary Metrics
Executive summary showing the overall fraud situation (all amounts in PKR).

```json
"summary": {
  "total_transactions_analyzed": 5000,
  "fraudulent_transactions_detected": 42,
  "fraud_percentage": 0.84,
  "total_fraud_amount": 285500000.00,
  "affected_accounts": 28,
  "high_risk_accounts": 8,
  "average_fraud_amount": 6797619.05,
  "max_fraud_amount": 950000000.00
}
```

**Fields:**
- `total_transactions_analyzed`: All transactions processed
- `fraudulent_transactions_detected`: Count of detected fraud transactions
- `fraud_percentage`: Fraud as % of total transactions
- `total_fraud_amount`: Sum of all fraudulent transaction amounts (PKR)
- `affected_accounts`: Number of accounts with at least one fraud
- `high_risk_accounts`: Accounts with fraud amount > ₨200,000
- `average_fraud_amount`: Mean fraud transaction amount (PKR)
- `max_fraud_amount`: Largest single fraud transaction (PKR)

### 2. Key Indicators
Critical risk indicators for quick decision-making.

```json
"key_indicators": {
  "fraud_severity_index": 45.67,
  "accounts_requiring_action": 15,
  "new_beneficiary_fraud_rate": 68.29,
  "risk_level": "HIGH",
  "action_urgency": "IMMEDIATE"
}
```

**Fields:**
- `fraud_severity_index`: Weighted score (0-100) incorporating amount, count, and fraud scores
- `accounts_requiring_action`: Accounts with fraud amount ≥ ₨200,000
- `new_beneficiary_fraud_rate`: % of frauds involving new beneficiaries (higher risk indicator)
- `risk_level`: Overall risk assessment (CRITICAL, HIGH, MEDIUM, LOW)
- `action_urgency`: How immediately action is needed (IMMEDIATE, HIGH, MEDIUM, LOW)

### 3. Actionable Alerts
Priority-ranked accounts requiring monitoring unit action.

```json
"actionable_alerts": {
  "total_alerts": 28,
  "critical_alerts": 2,
  "urgent_alerts": 5,
  "top_alerts": [
    {
      "account_number": "ACC00156",
      "total_fraud_amount": 950000000.00,
      "fraud_transaction_count": 3,
      "avg_fraud_score": 7.67,
      "risk_score": 1.52,
      "recommended_action": "BLOCK"
    },
    {
      "account_number": "ACC00289",
      "total_fraud_amount": 785000000.00,
      "fraud_transaction_count": 5,
      "avg_fraud_score": 6.80,
      "risk_score": 1.29,
      "recommended_action": "BLOCK"
    }
    // ... more accounts
  ]
}
```

**Fields:**
- `total_alerts`: Total affected accounts
- `critical_alerts`: Accounts flagged for blocking
- `urgent_alerts`: Accounts requiring urgent review
- `top_alerts`: Top 20 accounts sorted by fraud amount
  - `recommended_action`: Action to take:
    - **BLOCK** (amount ≥ ₨2,000,000 or ≥10 transactions)
    - **URGENT_REVIEW** (amount ₨500,000-2,000,000 or 5-10 transactions)
    - **CONTACT_CUSTOMER** (amount ₨200,000-500,000)
    - **MONITOR** (ongoing surveillance)

### 4. Fraud Distribution
Breakdown of fraud patterns by characteristics.

```json
"fraud_distribution": {
  "by_beneficiary_type": {
    "new_beneficiary": 28,
    "repeat_beneficiary": 14,
    "new_beneficiary_percentage": 66.67
  },
  "by_transaction_type": {
    "020": 15,
    "010": 18,
    "030": 9
  },
  "by_debit_credit": {
    "D": 42,
    "C": 0
  }
}
```

**Insights:**
- High `new_beneficiary_percentage` suggests targeted scams
- `by_transaction_type` helps identify vulnerable transaction types
- Mostly debits (D) suggests fund outflows (typical fraud pattern)

### 5. Top Affected Accounts
Concentration of risk analysis (amounts in PKR).

```json
"top_accounts": {
  "top_10_accounts": [
    {
      "rank": 1,
      "account_number": "ACC00156",
      "total_fraud_amount": 950000000.00,
      "fraud_transaction_count": 3,
      "avg_transaction_amount": 316666666.67,
      "avg_fraud_score": 7.67
    },
    // ... 9 more accounts
  ],
  "concentration_percentage": 72.45
}
```

**Insight:**
- `concentration_percentage`: % of total fraud from top 10 accounts
- High concentration (>70%) suggests few accounts are vulnerable to specific threats

### 6. Amount Distribution
Fraud amounts categorized by ranges for pattern analysis (in PKR).

```json
"amount_distribution": {
  "by_amount_range": {
    "0-1K": {
      "count": 8,
      "amount": 5500000.00,
      "percentage": 19.05
    },
    "1K-5K": {
      "count": 12,
      "amount": 42000000.00,
      "percentage": 28.57
    },
    "5K-10K": {
      "count": 10,
      "amount": 78000000.00,
      "percentage": 23.81
    },
    "10K-50K": {
      "count": 10,
      "amount": 250000000.00,
      "percentage": 23.81
    },
    "50K+": {
      "count": 2,
      "amount": 190000000.00,
      "percentage": 4.76
    }
  },
  "total_fraud_amount": 285500000.00
}
```

**Range Labels Explanation:**
- "0-1K" = 0 to ₨100,000
- "1K-5K" = ₨100,000 to ₨500,000
- "5K-10K" = ₨500,000 to ₨1,000,000
- "10K-50K" = ₨1,000,000 to ₨5,000,000
- "50K+" = ₨5,000,000 and above

**Insight:**
- Large high-amount frauds need different response than small frequent ones
- May indicate different types of threats or attack strategies

### 7. Temporal Analysis
Time-based patterns for identifying coordinated attacks or regular patterns.

```json
"temporal_analysis": {
  "by_hour": {
    "0": 2,
    "9": 8,
    "15": 9,
    "17": 7,
    // ... other hours
  },
  "by_day_of_week": {
    "Monday": 5,
    "Tuesday": 8,
    "Wednesday": 6,
    // ... other days
  },
  "peak_fraud_hour": 15
}
```

**Insight:**
- Peak fraud during business hours (9-5) vs off-hours suggests different threat types
- Day-of-week patterns may indicate timing correlations

### 8. Transaction Details
Sample of highest-risk individual transactions (amounts in PKR).

```json
"transaction_details": {
  "total_high_risk_transactions": 50,
  "sample_transactions": [
    {
      "account_number": "ACC00156",
      "transaction_id": "TXN000001",
      "timestamp": "01/01/2024 15:30:45",
      "amount": 450000000.00,
      "new_beneficiary": true,
      "device_id": "DEV_A1B2C3",
      "transaction_type_code": "020",
      "fraud_score": 8.5,
      "risk_level": "CRITICAL"
    },
    // ... more transactions
  ]
}
```

**Insight:**
- Individual transaction context for deeper investigation
- Transaction type code helps pattern matching

### 9. Metadata
Generation timestamp and processing information.

```json
"metadata": {
  "generated_at": "2024-01-01T15:45:30.123456",
  "total_records_processed": 5000,
  "total_frauds_detected": 42
}
```

## PKR Amount Thresholds

The dashboard uses the following action thresholds (in Pakistani Rupees):

| Action | Threshold | Details |
|--------|-----------|---------|
| **BLOCK** | ≥ ₨2,000,000 | Immediate account suspension |
| **URGENT_REVIEW** | ₨500,000 - ₨2,000,000 | Requires same-day investigation |
| **CONTACT_CUSTOMER** | ₨200,000 - ₨500,000 | Customer verification needed |
| **MONITOR** | < ₨200,000 | Ongoing surveillance |

Transaction Count Thresholds:
- **BLOCK**: ≥10 fraudulent transactions
- **URGENT_REVIEW**: 5-10 fraudulent transactions

## Usage Workflow

### Step 1: Generate Rules
```bash
POST /api/v1/generate-rules
- Input: 3 months of historical transaction data (CSV or Excel)
- Output: Rules file for date X
```

### Step 2: Detect Fraud
```bash
POST /api/v1/detect-fraud
- Input: New transaction data (CSV or Excel), detection date, rules date
- Output: fraud_detection_results_YYYYMMDD_HHMMSS.csv
```

### Step 3: Generate Dashboard Metrics
```bash
POST /api/v1/dashboard-metrics
- Input: fraud_detection_results_YYYYMMDD_HHMMSS.csv (or Excel file)
- Output: Comprehensive dashboard JSON with PKR amounts
```

## Supported File Formats

All endpoints support:
- **CSV** files (.csv)
- **Excel** files (.xlsx)

The system auto-detects the file format and processes accordingly.

## Example cURL Requests

### CSV File
```bash
curl -X POST "http://localhost:8000/api/v1/dashboard-metrics" \
  -F "file=@fraud_detection_results_20240101_203515.csv"
```

### Excel File
```bash
curl -X POST "http://localhost:8000/api/v1/dashboard-metrics" \
  -F "file=@fraud_detection_results.xlsx"
```

## Frontend Integration

The response can be directly used for frontend visualization:

1. **Executive Dashboard Card**: Use `summary` metrics (note PKR amounts)
2. **Risk Gauge**: Use `key_indicators.fraud_severity_index` (0-100 scale)
3. **Action Priority Table**: Use `actionable_alerts.top_alerts` with PKR thresholds
4. **Charts/Graphs**:
   - Pie chart: `fraud_distribution.by_beneficiary_type`
   - Bar chart: `fraud_distribution.by_transaction_type`
   - Heatmap: `temporal_analysis.by_hour` and `by_day_of_week`
   - Distribution chart: `amount_distribution.by_amount_range` with PKR ranges

## Error Handling

### Unsupported File Format
```json
{
  "detail": "File must be in CSV or Excel (.xlsx) format"
}
```

### Missing Required Columns
```json
{
  "detail": "Missing required columns in fraud detection results: {'rule_based_fraud_score', ...}"
}
```

### Server Error
```json
{
  "detail": "Error generating dashboard metrics: [error message]"
}
```

## Performance Notes

- Processing time depends on number of transactions (typically <5 seconds for 5K+ transactions)
- Response size is typically 100KB-500KB depending on transaction count
- All calculations are performed in-memory
- Excel files may be slightly slower than CSV due to parsing overhead

## Future Enhancements

When moving to real-time:
- Add time window filtering (last 1 hour, 24 hours, etc.)
- Implement incremental metric updates
- Add alerting thresholds
- Track metric trends over time
- Add support for other file formats (JSON, Parquet)
