"""
Sample Transaction Data Generator
Generates sample transaction data for testing the fraud detection system
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


def generate_sample_transactions(
    num_accounts: int = 100,
    num_days: int = 120,
    base_date: str = "01/01/2024"
):
    """
    Generate sample transaction data for testing
    
    Args:
        num_accounts: Number of unique accounts
        num_days: Number of days of transaction history
        base_date: Starting date in DD/MM/YYYY format
    
    Returns:
        DataFrame with sample transactions
    """
    
    start_date = datetime.strptime(base_date, "%d/%m/%Y")
    
    # Generate account numbers
    accounts = [f"ACC{str(i).zfill(6)}" for i in range(1, num_accounts + 1)]
    
    # Device IDs pool
    devices = [f"DEV{str(i).zfill(4)}" for i in range(1, 201)]
    
    # Transaction type codes
    transaction_codes = ['ezpsa', 'jzzcsh', 'nypy', 'other1', 'other2', 'other3', 'transfer', 'payment']
    
    transactions = []
    transaction_id = 1
    
    for account in accounts:
        # Each account has 1-2 primary devices
        primary_devices = random.sample(devices, k=random.randint(1, 2))
        
        # Determine normal transaction patterns
        avg_daily_txns = random.randint(1, 5)
        avg_txn_amount = random.randint(1000, 50000)
        
        # Favorite transaction hours
        favorite_hours = random.sample(range(8, 20), k=random.randint(2, 5))
        
        for day in range(num_days):
            current_date = start_date + timedelta(days=day)
            
            # Number of transactions this day
            num_txns = random.randint(0, avg_daily_txns + 3)
            
            for _ in range(num_txns):
                # Transaction timestamp
                if random.random() < 0.7:  # 70% in favorite hours
                    hour = random.choice(favorite_hours)
                else:
                    hour = random.randint(0, 23)
                
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = current_date.replace(hour=hour, minute=minute, second=second)
                
                # Credit or Debit (70% debit)
                cr_dr_ind = 'D' if random.random() < 0.7 else 'C'
                
                # Transaction amount
                if cr_dr_ind == 'D':
                    amount = abs(np.random.normal(avg_txn_amount, avg_txn_amount * 0.3))
                else:
                    amount = abs(np.random.normal(avg_txn_amount * 1.5, avg_txn_amount * 0.5))
                
                # Device (90% primary device)
                if random.random() < 0.9:
                    device = random.choice(primary_devices)
                else:
                    device = random.choice(devices)
                
                # New beneficiary flag (10% new)
                new_bene = 1 if random.random() < 0.1 else 0
                
                # Transaction type code
                txn_code = random.choice(transaction_codes)
                
                transactions.append({
                    'account_number': account,
                    'transaction_id': f"TXN{str(transaction_id).zfill(10)}",
                    'transaction_timestamp': timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                    'transaction_amount': round(amount, 2),
                    'cr_dr_ind': cr_dr_ind,
                    'New Beneficiary Flag': new_bene,
                    'device_id': device,
                    'transaction_type_code': txn_code
                })
                
                transaction_id += 1
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    
    # Sort by timestamp
    df['temp_timestamp'] = pd.to_datetime(df['transaction_timestamp'], format='%d/%m/%Y %H:%M:%S')
    df = df.sort_values('temp_timestamp').drop('temp_timestamp', axis=1).reset_index(drop=True)
    
    return df


def inject_fraudulent_transactions(df: pd.DataFrame, num_fraud: int = 50) -> pd.DataFrame:
    """
    Inject some fraudulent-looking transactions into the dataset
    
    Args:
        df: Original transaction dataframe
        num_fraud: Number of fraudulent transactions to inject
        
    Returns:
        DataFrame with fraudulent transactions added
    """
    
    fraud_transactions = []
    
    for _ in range(num_fraud):
        # Pick a random existing transaction as template
        template = df.sample(n=1).iloc[0].to_dict()
        
        # Modify to look fraudulent
        fraud_type = random.choice(['device_change', 'high_amount', 'unusual_hour', 'rapid_txns'])
        
        if fraud_type == 'device_change':
            # Change device and make it a new beneficiary
            template['device_id'] = f"DEV{str(random.randint(1, 200)).zfill(4)}"
            template['New Beneficiary Flag'] = 1
            template['transaction_amount'] = random.randint(50000, 200000)
            
        elif fraud_type == 'high_amount':
            # Very high transaction amount
            template['transaction_amount'] = random.randint(200000, 500000)
            
        elif fraud_type == 'unusual_hour':
            # Transaction at unusual hour (2-5 AM)
            timestamp = pd.to_datetime(template['transaction_timestamp'], format='%d/%m/%Y %H:%M:%S')
            timestamp = timestamp.replace(hour=random.randint(2, 5))
            template['transaction_timestamp'] = timestamp.strftime('%d/%m/%Y %H:%M:%S')
            template['transaction_amount'] = random.randint(60000, 150000)
            
        elif fraud_type == 'rapid_txns':
            # Multiple transactions in short time
            base_timestamp = pd.to_datetime(template['transaction_timestamp'], format='%d/%m/%Y %H:%M:%S')
            for i in range(5):
                txn = template.copy()
                new_timestamp = base_timestamp + timedelta(minutes=i*2)
                txn['transaction_timestamp'] = new_timestamp.strftime('%d/%m/%Y %H:%M:%S')
                txn['transaction_id'] = f"TXN{str(int(txn['transaction_id'][3:]) + 1000000 + i).zfill(10)}"
                txn['transaction_amount'] = random.randint(30000, 80000)
                fraud_transactions.append(txn)
            continue
        
        # Update transaction ID
        template['transaction_id'] = f"TXN{str(int(template['transaction_id'][3:]) + 1000000).zfill(10)}"
        template['cr_dr_ind'] = 'D'  # Make sure it's debit
        
        fraud_transactions.append(template)
    
    # Add fraudulent transactions
    if fraud_transactions:
        fraud_df = pd.DataFrame(fraud_transactions)
        df = pd.concat([df, fraud_df], ignore_index=True)
        
        # Sort by timestamp
        df['temp_timestamp'] = pd.to_datetime(df['transaction_timestamp'], format='%d/%m/%Y %H:%M:%S')
        df = df.sort_values('temp_timestamp').drop('temp_timestamp', axis=1).reset_index(drop=True)
    
    return df


if __name__ == "__main__":
    # Generate sample data
    print("Generating sample transaction data...")
    df = generate_sample_transactions(num_accounts=50, num_days=120, base_date="01/10/2023")
    
    print(f"Generated {len(df)} transactions")
    
    # Inject some fraudulent transactions
    print("Injecting fraudulent transactions...")
    df = inject_fraudulent_transactions(df, num_fraud=30)
    
    print(f"Total transactions (with fraud): {len(df)}")
    
    # Save to CSV
    output_file = "sample_transactions.csv"
    df.to_csv(output_file, index=False)
    print(f"Sample data saved to: {output_file}")
    
    # Print summary
    print("\nData Summary:")
    print(f"Date range: {df['transaction_timestamp'].min()} to {df['transaction_timestamp'].max()}")
    print(f"Unique accounts: {df['account_number'].nunique()}")
    print(f"Total transactions: {len(df)}")
    print(f"Debit transactions: {len(df[df['cr_dr_ind'] == 'D'])}")
    print(f"Credit transactions: {len(df[df['cr_dr_ind'] == 'C'])}")
