"""
Fraud Rules Generator
Generates account-level fraud detection rules from historical transaction data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Tuple
from config import IQR_MULTIPLIER, MIN_TRANSACTIONS_FOR_STATS

logger = logging.getLogger(__name__)


class FraudRulesGenerator:
    """Generates fraud detection rules from historical transaction data"""
    
    def __init__(self):
        self.iqr_multiplier = IQR_MULTIPLIER
        
    def generate_rules(self, df: pd.DataFrame, reference_date: datetime) -> pd.DataFrame:
        """
        Generate fraud detection rules for each account based on 3 months of historical data
        
        Args:
            df: Transaction dataframe
            reference_date: Reference date for rule generation
            
        Returns:
            DataFrame with rules for each account
        """
        logger.info("Starting rules generation...")
        
        # Parse transaction timestamp
        df['transaction_timestamp'] = pd.to_datetime(
            df['transaction_timestamp'], 
            format='%d/%m/%Y %H:%M:%S'
        )
        
        # Filter data: 3 months before reference date
        start_date = reference_date - timedelta(days=90)
        df_filtered = df[
            (df['transaction_timestamp'] >= start_date) & 
            (df['transaction_timestamp'] < reference_date)
        ].copy()
        
        logger.info(f"Filtered data: {len(df_filtered)} transactions between {start_date} and {reference_date}")
        
        # Filter only DEBIT transactions for rule generation
        df_debit = df_filtered[df_filtered['cr_dr_ind'].str.upper() == 'D'].copy()
        logger.info(f"Debit transactions: {len(df_debit)}")
        
        # Extract features
        df_debit['transaction_date'] = df_debit['transaction_timestamp'].dt.date
        df_debit['transaction_hour'] = df_debit['transaction_timestamp'].dt.hour
        
        # Get unique accounts
        accounts = df_debit['account_number'].unique()
        logger.info(f"Processing rules for {len(accounts)} accounts")
        
        # Generate rules for each account
        rules_list = []
        for account in accounts:
            account_df = df_debit[df_debit['account_number'] == account]
            account_rules = self._generate_account_rules(account_df, reference_date)
            rules_list.append(account_rules)
        
        rules_df = pd.DataFrame(rules_list)
        logger.info(f"Rules generated for {len(rules_df)} accounts")
        
        return rules_df
    
    def _generate_account_rules(self, account_df: pd.DataFrame, reference_date: datetime) -> dict:
        """Generate rules for a single account"""
        
        account_number = account_df['account_number'].iloc[0]
        rules = {'account_number': account_number}
        
        # 1. Most frequent device IDs
        rules.update(self._calculate_frequent_devices(account_df, reference_date))
        
        # 2. Daily debit transaction count statistics
        rules.update(self._calculate_daily_debit_count_stats(account_df))
        
        # 3. Daily debit amount statistics
        rules.update(self._calculate_daily_debit_amount_stats(account_df))
        
        # 4. Transaction amount statistics
        rules.update(self._calculate_txn_amount_stats(account_df))
        
        # 5. Hourly debit transaction count statistics
        rules.update(self._calculate_hourly_count_stats(account_df))
        
        # 6. Hour-wise transaction percentages
        rules.update(self._calculate_hour_percentages(account_df))
        
        return rules
    
    def _calculate_frequent_devices(self, df: pd.DataFrame, reference_date: datetime) -> dict:
        """Calculate most frequent device IDs for weekly and monthly windows"""
        
        # Most frequent device in last 7 days
        week_start = reference_date - timedelta(days=7)
        weekly_df = df[df['transaction_timestamp'] >= week_start]
        
        if len(weekly_df) > 0:
            most_freq_devid_wkly = weekly_df['device_id'].mode()[0] if len(weekly_df['device_id'].mode()) > 0 else None
        else:
            most_freq_devid_wkly = None
        
        # Most frequent device in last 30 days
        month_start = reference_date - timedelta(days=30)
        monthly_df = df[df['transaction_timestamp'] >= month_start]
        
        if len(monthly_df) > 0:
            most_freq_devid_1m = monthly_df['device_id'].mode()[0] if len(monthly_df['device_id'].mode()) > 0 else None
        else:
            most_freq_devid_1m = None
        
        return {
            'most_freq_devid_wkly': most_freq_devid_wkly,
            'most_freq_devid_1m': most_freq_devid_1m
        }
    
    def _calculate_daily_debit_count_stats(self, df: pd.DataFrame) -> dict:
        """Calculate daily debit transaction count statistics"""
        
        # Group by date and count transactions
        daily_counts = df.groupby('transaction_date').size()
        
        if len(daily_counts) >= MIN_TRANSACTIONS_FOR_STATS:
            p25 = daily_counts.quantile(0.25)
            p50 = daily_counts.quantile(0.50)
            p75 = daily_counts.quantile(0.75)
            p90 = daily_counts.quantile(0.90)
            
            # Calculate upper bound using IQR
            iqr = p75 - p25
            upper_bound = p75 + (self.iqr_multiplier * iqr)
        else:
            p25 = p50 = p75 = p90 = upper_bound = 0
        
        return {
            'daily_debit_txn_count_p25': p25,
            'daily_debit_txn_count_p50': p50,
            'daily_debit_txn_count_p75': p75,
            'daily_debit_txn_count_p90': p90,
            'daily_debit_txn_count_upper_bound': upper_bound
        }
    
    def _calculate_daily_debit_amount_stats(self, df: pd.DataFrame) -> dict:
        """Calculate daily debit amount statistics"""
        
        # Group by date and sum amounts
        daily_amounts = df.groupby('transaction_date')['transaction_amount'].sum()
        
        if len(daily_amounts) >= MIN_TRANSACTIONS_FOR_STATS:
            p25 = daily_amounts.quantile(0.25)
            p50 = daily_amounts.quantile(0.50)
            p75 = daily_amounts.quantile(0.75)
            p90 = daily_amounts.quantile(0.90)
            
            # Calculate upper bound using IQR
            iqr = p75 - p25
            upper_bound = p75 + (self.iqr_multiplier * iqr)
        else:
            p25 = p50 = p75 = p90 = upper_bound = 0
        
        return {
            'daily_debit_amt_p25': p25,
            'daily_debit_amt_p50': p50,
            'daily_debit_amt_p75': p75,
            'daily_debit_amt_p90': p90,
            'daily_debit_amt_upper_bound': upper_bound
        }
    
    def _calculate_txn_amount_stats(self, df: pd.DataFrame) -> dict:
        """Calculate transaction amount statistics"""
        
        amounts = df['transaction_amount']
        
        if len(amounts) >= MIN_TRANSACTIONS_FOR_STATS:
            p25 = amounts.quantile(0.25)
            p50 = amounts.quantile(0.50)
            p75 = amounts.quantile(0.75)
            p90 = amounts.quantile(0.90)
            
            # Calculate upper bound using IQR
            iqr = p75 - p25
            upper_bound = p75 + (self.iqr_multiplier * iqr)
        else:
            p25 = p50 = p75 = p90 = upper_bound = 0
        
        return {
            'txn_amt_p25': p25,
            'txn_amt_p50': p50,
            'txn_amt_p75': p75,
            'txn_amt_p90': p90,
            'txn_amt_upper_bound': upper_bound
        }
    
    def _calculate_hourly_count_stats(self, df: pd.DataFrame) -> dict:
        """Calculate hourly transaction count statistics"""
        
        # Create datetime with date and hour
        df_temp = df.copy()
        df_temp['date_hour'] = df_temp['transaction_timestamp'].dt.floor('H')
        
        # Group by date_hour and count transactions
        hourly_counts = df_temp.groupby('date_hour').size()
        
        if len(hourly_counts) >= MIN_TRANSACTIONS_FOR_STATS:
            p25 = hourly_counts.quantile(0.25)
            p50 = hourly_counts.quantile(0.50)
            p75 = hourly_counts.quantile(0.75)
            p90 = hourly_counts.quantile(0.90)
            
            # Calculate upper bound using IQR
            iqr = p75 - p25
            upper_bound = p75 + (self.iqr_multiplier * iqr)
        else:
            p25 = p50 = p75 = p90 = upper_bound = 0
        
        return {
            'hourly_debit_transaction_count_p25': p25,
            'hourly_debit_transaction_count_p50': p50,
            'hourly_debit_transaction_count_p75': p75,
            'hourly_debit_transaction_count_p90': p90,
            'hourly_debit_transaction_count_upper_bound': upper_bound
        }
    
    def _calculate_hour_percentages(self, df: pd.DataFrame) -> dict:
        """Calculate percentage of transactions for each hour (0-23)"""
        
        total_transactions = len(df)
        hour_percentages = {}
        
        if total_transactions > 0:
            hour_counts = df['transaction_hour'].value_counts()
            
            for hour in range(24):
                count = hour_counts.get(hour, 0)
                percentage = (count / total_transactions) if total_transactions > 0 else 0
                hour_percentages[f'hour_{hour}_pct'] = percentage
        else:
            for hour in range(24):
                hour_percentages[f'hour_{hour}_pct'] = 0
        
        return hour_percentages
