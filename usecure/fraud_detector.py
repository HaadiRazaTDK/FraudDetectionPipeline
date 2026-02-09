"""
Fraud Detector
Applies fraud detection rules to real-time transactions
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List
from config import (
    MICROFINANCE_TRANSACTION_CODES, 
    FRAUD_DETECTION_CONFIG
)

logger = logging.getLogger(__name__)


class FraudDetector:
    """Detects fraud in transactions using pre-generated rules"""
    
    def __init__(self, rules_df: pd.DataFrame):
        """
        Initialize fraud detector with rules
        
        Args:
            rules_df: DataFrame containing fraud detection rules for each account
        """
        self.rules_df = rules_df
        self.microfinance_codes = MICROFINANCE_TRANSACTION_CODES
        self.config = FRAUD_DETECTION_CONFIG
        
        # Create a dictionary for fast rule lookup
        self.rules_dict = rules_df.set_index('account_number').to_dict('index')
        logger.info(f"Loaded rules for {len(self.rules_dict)} accounts")
    
    def detect_fraud(self, df: pd.DataFrame, detection_date: datetime) -> pd.DataFrame:
        """
        Detect fraud in transactions for a specific date
        
        Args:
            df: Transaction dataframe
            detection_date: Date to detect fraud for
            
        Returns:
            DataFrame with fraud detection results
        """
        logger.info(f"Starting fraud detection for date: {detection_date}")
        
        # Parse transaction timestamp
        df['transaction_timestamp'] = pd.to_datetime(
            df['transaction_timestamp'], 
            format='%d/%m/%Y %H:%M:%S'
        )
        
        # Filter transactions for the detection date (only DEBIT transactions)
        df_filtered = df[
            (df['transaction_timestamp'].dt.date == detection_date.date()) &
            (df['cr_dr_ind'].str.upper() == 'D')
        ].copy()
        
        logger.info(f"Processing {len(df_filtered)} debit transactions for {detection_date.date()}")
        
        # Sort by timestamp to process chronologically
        df_filtered = df_filtered.sort_values('transaction_timestamp').reset_index(drop=True)
        
        # Extract hour from timestamp
        df_filtered['transaction_hour'] = df_filtered['transaction_timestamp'].dt.hour
        
        # Calculate real-time features
        df_filtered = self._calculate_realtime_features(df_filtered)
        
        # Apply fraud detection rules
        df_filtered = self._apply_fraud_rules(df_filtered)
        
        # Select output columns
        output_columns = self._get_output_columns(df_filtered)
        
        logger.info(f"Fraud detection completed. {df_filtered['rule_based_fraud_detected'].sum()} fraudulent transactions detected")
        
        return df_filtered[output_columns]
    
    def _calculate_realtime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cumulative features for real-time fraud detection"""
        
        logger.info("Calculating real-time features...")
        
        # Initialize columns
        df['cumulative_daily_amount'] = 0.0
        df['cumulative_daily_count'] = 0
        df['cumulative_hourly_count'] = 0
        df['cumulative_microfinance_daily_amount'] = 0.0
        df['first_destination_new_logic'] = df['New Beneficiary Flag']
        df['device_id_current'] = df['device_id']
        df['transaction_value'] = df['transaction_amount']
        
        # Process transactions chronologically for each account
        for account in df['account_number'].unique():
            account_mask = df['account_number'] == account
            account_indices = df[account_mask].index
            
            # Track cumulative values
            daily_amount = 0.0
            daily_count = 0
            microfinance_amount = 0.0
            hour_counts = {}
            
            for idx in account_indices:
                row = df.loc[idx]
                
                # Update cumulative daily amount and count
                daily_amount += row['transaction_amount']
                daily_count += 1
                
                df.at[idx, 'cumulative_daily_amount'] = daily_amount
                df.at[idx, 'cumulative_daily_count'] = daily_count
                
                # Update cumulative hourly count
                current_hour = row['transaction_hour']
                hour_counts[current_hour] = hour_counts.get(current_hour, 0) + 1
                df.at[idx, 'cumulative_hourly_count'] = hour_counts[current_hour]
                
                # Update cumulative microfinance amount
                if row['transaction_type_code'] in self.microfinance_codes:
                    microfinance_amount += row['transaction_amount']
                
                df.at[idx, 'cumulative_microfinance_daily_amount'] = microfinance_amount
        
        return df
    
    def _apply_fraud_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all fraud detection rules to transactions"""
        
        logger.info("Applying fraud detection rules...")
        
        # Merge with rules
        df = df.merge(
            self.rules_df,
            on='account_number',
            how='left'
        )
        
        # For accounts without rules, fill with default values
        df = df.fillna({
            'most_freq_devid_wkly': '',
            'most_freq_devid_1m': '',
            'daily_debit_txn_count_upper_bound': 999999,
            'daily_debit_amt_upper_bound': 999999999,
            'daily_debit_amt_p50': 0,
            'txn_amt_upper_bound': 999999999,
            'hourly_debit_transaction_count_upper_bound': 999999,
        })
        
        # Fill hour percentages with 0
        for hour in range(24):
            df[f'hour_{hour}_pct'] = df[f'hour_{hour}_pct'].fillna(0)
        
        # RULE 1: Device ID Change Detection
        df['fraud_device_change'] = (
            (df['device_id_current'] != df['most_freq_devid_wkly']) |
            (df['device_id_current'] != df['most_freq_devid_1m'])
        ).astype(int)
        
        # RULE 2: Daily Debit Count Exceeds Upper Bound
        df['fraud_daily_debit_count'] = (
            (df['cumulative_daily_count'] > df['daily_debit_txn_count_upper_bound']) &
            (df['cumulative_daily_count'] >= self.config['minimum_daily_debit_count'])
        ).astype(int)
        
        # RULE 3: Daily Debit Amount Exceeds Upper Bound
        df['fraud_daily_debit_amt'] = (
            df['cumulative_daily_amount'] > df['daily_debit_amt_upper_bound']
        ).astype(int)
        
        # RULE 4: Transaction Amount Exceeds Upper Bound
        df['fraud_txn_amt'] = (
            (df['transaction_value'] > df['txn_amt_upper_bound']) &
            (df['transaction_value'] > self.config['high_transaction_amount_threshold'])
        ).astype(int)
        
        # RULE 5: Hourly Transaction Count Exceeds Upper Bound
        df['fraud_hourly_count'] = (
            (df['cumulative_hourly_count'] > df['hourly_debit_transaction_count_upper_bound']) &
            (df['cumulative_hourly_count'] >= self.config['minimum_hourly_count'])
        ).astype(int)
        
        # RULE 6: New Beneficiary with High Transaction Amount
        df['fraud_new_bene_high_transaction'] = (
            (df['transaction_value'] > df['daily_debit_amt_p50']) &
            (df['first_destination_new_logic'] == 1)
        ).astype(int)
        
        # RULE 7: Unusual Hour Detection
        df['fraud_unusual_hour'] = self._apply_unusual_hour_rule(df)
        
        # RULE 8: Device Change + New Beneficiary + Microfinance >= 75k
        df['fraud_device_change_new_bene_bb_75k'] = (
            (df['fraud_device_change'] == 1) &
            (df['cumulative_microfinance_daily_amount'] >= self.config['device_change_microfinance_threshold']) &
            (df['first_destination_new_logic'] == 1)
        ).astype(int)
        
        # Calculate fraud score
        df['rule_based_fraud_score'] = (
            df['fraud_device_change'] +
            df['fraud_daily_debit_count'] +
            df['fraud_daily_debit_amt'] +
            df['fraud_txn_amt'] +
            df['fraud_hourly_count'] +
            df['fraud_unusual_hour'] +
            df['fraud_new_bene_high_transaction'] +
            df['fraud_device_change_new_bene_bb_75k']
        )
        
        # Final fraud detection
        # Fraud if score >= 3 OR fraud_new_bene_high_transaction is True
        df['rule_based_fraud_detected'] = (
            (df['rule_based_fraud_score'] >= self.config['minimum_fraud_score']) |
            (df['fraud_new_bene_high_transaction'] == 1)
        )
        
        return df
    
    def _apply_unusual_hour_rule(self, df: pd.DataFrame) -> pd.Series:
        """Apply unusual hour detection rule"""
        
        conditions = []
        threshold = self.config['unusual_hour_amount_threshold']
        
        # Build condition for each hour
        for hour in range(24):
            hour_condition = (
                (df['transaction_value'] >= threshold) &
                (df['transaction_hour'] == hour) &
                (df[f'hour_{hour}_pct'] == 0)
            )
            conditions.append(hour_condition)
        
        # Combine all conditions with OR
        unusual_hour_flag = pd.Series(False, index=df.index)
        for condition in conditions:
            unusual_hour_flag = unusual_hour_flag | condition
        
        return unusual_hour_flag.astype(int)
    
    def _get_output_columns(self, df: pd.DataFrame) -> List[str]:
        """Define output columns for the result CSV"""
        
        # Core transaction columns
        core_columns = [
            'account_number',
            'transaction_id',
            'transaction_timestamp',
            'transaction_amount',
            'cr_dr_ind',
            'New Beneficiary Flag',
            'device_id',
            'transaction_type_code'
        ]
        
        # Real-time calculated features
        realtime_features = [
            'transaction_hour',
            'first_destination_new_logic',
            'device_id_current',
            'cumulative_daily_amount',
            'cumulative_daily_count',
            'cumulative_hourly_count',
            'transaction_value',
            'cumulative_microfinance_daily_amount'
        ]
        
        # Rule flags
        rule_flags = [
            'fraud_device_change',
            'fraud_daily_debit_count',
            'fraud_daily_debit_amt',
            'fraud_txn_amt',
            'fraud_hourly_count',
            'fraud_new_bene_high_transaction',
            'fraud_unusual_hour',
            'fraud_device_change_new_bene_bb_75k'
        ]
        
        # Final detection columns
        detection_columns = [
            'rule_based_fraud_score',
            'rule_based_fraud_detected'
        ]
        
        # Account rules (for reference)
        rule_columns = [
            'most_freq_devid_wkly',
            'most_freq_devid_1m',
            'daily_debit_txn_count_upper_bound',
            'daily_debit_amt_upper_bound',
            'daily_debit_amt_p50',
            'txn_amt_upper_bound',
            'hourly_debit_transaction_count_upper_bound'
        ]
        
        # Combine all columns
        all_columns = (
            core_columns + 
            realtime_features + 
            rule_columns + 
            rule_flags + 
            detection_columns
        )
        
        # Return only columns that exist in dataframe
        return [col for col in all_columns if col in df.columns]
