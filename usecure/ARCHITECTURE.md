# UBL Fraud Detection System - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  • Web Browser (Swagger UI)                                      │
│  • Postman / cURL                                                │
│  • Python Scripts                                                │
│  • Internal Applications                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION                          │
├─────────────────────────────────────────────────────────────────┤
│  main.py (API Endpoints)                                         │
│  ├── POST /api/v1/generate-rules                                 │
│  ├── POST /api/v1/detect-fraud                                   │
│  └── GET  /api/v1/rules/list                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  FraudRulesGenerator                    FraudDetector            │
│  ├── generate_rules()                   ├── detect_fraud()       │
│  ├── _calculate_frequent_devices()      ├── _apply_fraud_rules() │
│  ├── _calculate_daily_stats()           ├── _calculate_realtime_ │
│  ├── _calculate_hourly_stats()          │   features()           │
│  └── _calculate_hour_percentages()      └── _apply_unusual_hour_ │
│                                              rule()               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  CSV Files (File System)                                         │
│  ├── /rules/          → Generated rules files                    │
│  ├── /output/         → Fraud detection results                  │
│  └── /temp/           → Temporary processing files               │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Rules Generation Flow

```
┌─────────────┐
│   Client    │
│  Uploads    │
│ CSV + Date  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│  1. Validate Input                  │
│     - Check date format             │
│     - Verify required columns       │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  2. Parse Transactions              │
│     - Convert timestamps            │
│     - Filter date range (3 months)  │
│     - Filter DEBIT transactions     │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  3. Group by Account                │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  4. Calculate Rules (Per Account)   │
│     ┌───────────────────────────┐   │
│     │ Device Frequency          │   │
│     │  - Last 7 days            │   │
│     │  - Last 30 days           │   │
│     └───────────────────────────┘   │
│     ┌───────────────────────────┐   │
│     │ Daily Debit Stats         │   │
│     │  - Count percentiles      │   │
│     │  - Amount percentiles     │   │
│     │  - Upper bounds (IQR)     │   │
│     └───────────────────────────┘   │
│     ┌───────────────────────────┐   │
│     │ Transaction Amount Stats  │   │
│     │  - Percentiles            │   │
│     │  - Upper bound            │   │
│     └───────────────────────────┘   │
│     ┌───────────────────────────┐   │
│     │ Hourly Stats              │   │
│     │  - Count percentiles      │   │
│     │  - Upper bound            │   │
│     └───────────────────────────┘   │
│     ┌───────────────────────────┐   │
│     │ Hour Distribution         │   │
│     │  - % for each hour (0-23) │   │
│     └───────────────────────────┘   │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  5. Save Rules to CSV               │
│     /rules/fraud_rules_YYYYMMDD.csv │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  6. Return Success Response         │
│     - Rules filename                │
│     - Accounts processed            │
│     - Date range                    │
└─────────────────────────────────────┘
```

### 2. Fraud Detection Flow

```
┌─────────────┐
│   Client    │
│  Uploads    │
│ CSV + Dates │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│  1. Validate Input                  │
│     - Check date formats            │
│     - Verify rules file exists      │
│     - Verify required columns       │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  2. Load Rules                      │
│     - Read rules CSV                │
│     - Create lookup dictionary      │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  3. Parse & Filter Transactions     │
│     - Convert timestamps            │
│     - Filter detection date         │
│     - Filter DEBIT transactions     │
│     - Sort by timestamp (chrono)    │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  4. Calculate Real-time Features    │
│     (Process Chronologically)       │
│     ┌───────────────────────────┐   │
│     │ For Each Transaction:     │   │
│     │  - Extract hour           │   │
│     │  - Get current device     │   │
│     │  - Update cumulative:     │   │
│     │    • Daily amount         │   │
│     │    • Daily count          │   │
│     │    • Hourly count         │   │
│     │    • Microfinance amount  │   │
│     └───────────────────────────┘   │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  5. Merge with Account Rules        │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  6. Apply Fraud Rules               │
│     ┌───────────────────────────┐   │
│     │ Rule 1: Device Change     │   │
│     │ Rule 2: Daily Debit Count │   │
│     │ Rule 3: Daily Debit Amt   │   │
│     │ Rule 4: Transaction Amt   │   │
│     │ Rule 5: Hourly Count      │   │
│     │ Rule 6: New Bene High Txn │   │
│     │ Rule 7: Unusual Hour      │   │
│     │ Rule 8: Device+Bene+BB    │   │
│     └───────────────────────────┘   │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  7. Calculate Fraud Score           │
│     - Sum all rule flags            │
│     - Determine fraud detection     │
│     - Score >= 3 OR Rule 6 = TRUE   │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  8. Save Results to CSV             │
│     /output/fraud_detection_...csv  │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  9. Return CSV Download             │
└─────────────────────────────────────┘
```

## Component Details

### 1. Main Application (main.py)

**Responsibilities**:
- HTTP request handling
- Input validation
- File upload processing
- Response formatting
- Error handling

**Key Functions**:
```python
@app.post("/api/v1/generate-rules")
async def generate_rules(file, input_date)

@app.post("/api/v1/detect-fraud")
async def detect_fraud(file, detection_date, rules_date)

@app.get("/api/v1/rules/list")
async def list_rules()
```

### 2. Fraud Rules Generator (fraud_rules_generator.py)

**Responsibilities**:
- Historical data analysis
- Statistical calculations
- Rule generation per account

**Key Methods**:
```python
class FraudRulesGenerator:
    def generate_rules(df, reference_date)
    def _generate_account_rules(account_df, reference_date)
    def _calculate_frequent_devices(df, reference_date)
    def _calculate_daily_debit_count_stats(df)
    def _calculate_daily_debit_amount_stats(df)
    def _calculate_txn_amount_stats(df)
    def _calculate_hourly_count_stats(df)
    def _calculate_hour_percentages(df)
```

**Statistical Method**: IQR (Interquartile Range)
```
Upper Bound = P75 + (1.5 × IQR)
Where: IQR = P75 - P25
```

### 3. Fraud Detector (fraud_detector.py)

**Responsibilities**:
- Real-time feature calculation
- Rule application
- Fraud scoring
- Result compilation

**Key Methods**:
```python
class FraudDetector:
    def detect_fraud(df, detection_date)
    def _calculate_realtime_features(df)
    def _apply_fraud_rules(df)
    def _apply_unusual_hour_rule(df)
    def _get_output_columns(df)
```

**Processing Strategy**: Chronological
- Transactions sorted by timestamp
- Cumulative metrics calculated sequentially
- Ensures accurate running totals

### 4. Configuration (config.py)

**Settings**:
```python
# Directories
RULES_DIR = "rules"
OUTPUT_DIR = "output"
TEMP_DIR = "temp"

# Configurable transaction codes
MICROFINANCE_TRANSACTION_CODES = ['ezpsa', 'jzzcsh', 'nypy']

# IQR multiplier
IQR_MULTIPLIER = 1.5

# Detection thresholds
FRAUD_DETECTION_CONFIG = {
    'minimum_fraud_score': 3,
    'unusual_hour_amount_threshold': 49999,
    'high_transaction_amount_threshold': 200000,
    'minimum_daily_debit_count': 3,
    'minimum_hourly_count': 3,
    'device_change_microfinance_threshold': 75000
}
```

## Fraud Detection Logic

### Rule Evaluation Matrix

| Rule | Condition | Score | Special |
|------|-----------|-------|---------|
| Device Change | device ≠ frequent_device | 1 | - |
| Daily Debit Count | count > upper_bound AND ≥ 3 | 1 | - |
| Daily Debit Amount | amount > upper_bound | 1 | - |
| Transaction Amount | txn > upper_bound AND > 200k | 1 | - |
| Hourly Count | count > upper_bound AND ≥ 3 | 1 | - |
| New Bene High Txn | txn > p50 AND new_bene = 1 | 1 | Triggers fraud independently |
| Unusual Hour | txn ≥ 49,999 AND hour_pct = 0 | 1 | - |
| Device+Bene+BB | device_change AND new_bene AND microfinance ≥ 75k | 1 | - |

### Final Decision Logic

```python
fraud_detected = (
    (fraud_score >= 3) OR
    (fraud_new_bene_high_transaction == True)
)
```

**Interpretation**:
- Score 0-2: Normal
- Score 3-4: Medium risk
- Score 5-6: High risk
- Score 7-8: Critical risk
- Rule 6 alone: High risk (new beneficiary)

## Data Schema

### Input Schema (CSV)

```
Column Name              Type        Required    Description
──────────────────────────────────────────────────────────────
account_number           String      Yes         Account identifier
transaction_id           String      Yes         Unique transaction ID
transaction_timestamp    DateTime    Yes         DD/MM/YYYY HH:MM:SS
transaction_amount       Float       Yes         Transaction amount
cr_dr_ind               Char        Yes         C (credit) / D (debit)
New Beneficiary Flag     Integer     Yes         0 (existing) / 1 (new)
device_id               String      Yes         Device identifier
transaction_type_code    String      Yes         Transaction type
```

### Rules Schema (Generated CSV)

```
Column Name                                Type    Description
────────────────────────────────────────────────────────────────
account_number                             String  Account identifier
most_freq_devid_wkly                       String  Most frequent device (7 days)
most_freq_devid_1m                         String  Most frequent device (30 days)
daily_debit_txn_count_p25                  Float   25th percentile
daily_debit_txn_count_p50                  Float   50th percentile
daily_debit_txn_count_p75                  Float   75th percentile
daily_debit_txn_count_p90                  Float   90th percentile
daily_debit_txn_count_upper_bound          Float   Upper bound (IQR)
daily_debit_amt_p25                        Float   25th percentile
daily_debit_amt_p50                        Float   50th percentile
daily_debit_amt_p75                        Float   75th percentile
daily_debit_amt_p90                        Float   90th percentile
daily_debit_amt_upper_bound                Float   Upper bound (IQR)
txn_amt_p25                                Float   25th percentile
txn_amt_p50                                Float   50th percentile
txn_amt_p75                                Float   75th percentile
txn_amt_p90                                Float   90th percentile
txn_amt_upper_bound                        Float   Upper bound (IQR)
hourly_debit_transaction_count_p25         Float   25th percentile
hourly_debit_transaction_count_p50         Float   50th percentile
hourly_debit_transaction_count_p75         Float   75th percentile
hourly_debit_transaction_count_p90         Float   90th percentile
hourly_debit_transaction_count_upper_bound Float   Upper bound (IQR)
hour_0_pct ... hour_23_pct                 Float   % transactions per hour
```

### Output Schema (Detection Results CSV)

```
Includes all input columns +
Includes all rules columns +

Real-time Features:
- transaction_hour
- first_destination_new_logic
- device_id_current
- cumulative_daily_amount
- cumulative_daily_count
- cumulative_hourly_count
- transaction_value
- cumulative_microfinance_daily_amount

Fraud Flags (0/1):
- fraud_device_change
- fraud_daily_debit_count
- fraud_daily_debit_amt
- fraud_txn_amt
- fraud_hourly_count
- fraud_new_bene_high_transaction
- fraud_unusual_hour
- fraud_device_change_new_bene_bb_75k

Final Detection:
- rule_based_fraud_score (Integer: 0-8)
- rule_based_fraud_detected (Boolean: True/False)
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid input (date format, missing columns) |
| 404 | Not Found | Rules file doesn't exist |
| 500 | Server Error | Internal processing error |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

## Security Considerations

### Current Implementation (POC)
- No authentication
- No authorization
- No rate limiting
- No input sanitization beyond basic validation
- No encryption

### Production Recommendations
1. **Authentication**: JWT tokens or OAuth2
2. **Authorization**: Role-based access control
3. **Rate Limiting**: API throttling
4. **Input Validation**: Strict schema validation
5. **Encryption**: HTTPS/TLS
6. **Logging**: Audit trails
7. **Monitoring**: Real-time alerts

## Performance Characteristics

### Time Complexity

**Rules Generation**:
- O(n log n) for sorting transactions
- O(n) for statistical calculations per account
- Overall: O(n log n) where n = total transactions

**Fraud Detection**:
- O(n log n) for sorting by timestamp
- O(n) for chronological processing
- O(n) for rule application
- Overall: O(n log n) where n = transactions on detection date

### Space Complexity

**Rules Generation**:
- O(n) for input data
- O(a) for rules output where a = number of accounts
- Overall: O(n + a)

**Fraud Detection**:
- O(n) for input data
- O(n) for results output
- Overall: O(n)

### Scalability Limits

**Current Implementation**:
- Memory-bound: All data loaded in memory
- Single-threaded processing
- File-based storage

**Recommended for**:
- < 1M transactions per day
- < 100K accounts
- < 10 concurrent users

**For Higher Scale**:
- Database storage (PostgreSQL)
- Distributed processing (Spark)
- Caching layer (Redis)
- Message queue (Kafka)

## Deployment Architecture (Recommended)

```
┌──────────────────────────────────────────────┐
│              Load Balancer                    │
│           (Nginx / AWS ALB)                   │
└────────────────┬─────────────────────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
┌──────▼──────┐    ┌──────▼──────┐
│ FastAPI     │    │ FastAPI     │
│ Instance 1  │    │ Instance 2  │
└──────┬──────┘    └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │   PostgreSQL DB   │
       │   (Rules & Logs)  │
       └───────────────────┘
```

---

**Version**: 1.0.0  
**Last Updated**: February 2026
