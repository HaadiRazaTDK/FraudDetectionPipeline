"""
Configuration settings for the fraud detection system
"""
import os

# Directories
RULES_DIR = os.path.join(os.getcwd(), "rules")
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
TEMP_DIR = os.path.join(os.getcwd(), "temp")

# Microfinance transaction codes (configurable)
MICROFINANCE_TRANSACTION_CODES = ['ezpsa', 'jzzcsh', 'nypy']

# IQR multiplier for upper bound calculation
IQR_MULTIPLIER = 1.5

# Minimum transaction thresholds
MIN_TRANSACTIONS_FOR_STATS = 5

# Column name mappings
COLUMN_MAPPING = {
    'input': {
        'account_number': 'account_number',
        'transaction_id': 'transaction_id',
        'transaction_timestamp': 'transaction_timestamp',
        'transaction_amount': 'transaction_amount',
        'cr_dr_ind': 'cr_dr_ind',
        'new_beneficiary_flag': 'New Beneficiary Flag',
        'device_id': 'device_id',
        'transaction_type_code': 'transaction_type_code'
    }
}

# Fraud detection thresholds
FRAUD_DETECTION_CONFIG = {
    'minimum_fraud_score': 3,
    'unusual_hour_amount_threshold': 49999,
    'high_transaction_amount_threshold': 200000,
    'minimum_daily_debit_count': 3,
    'minimum_hourly_count': 3,
    'device_change_microfinance_threshold': 75000
}
