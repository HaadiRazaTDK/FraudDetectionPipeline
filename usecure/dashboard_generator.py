"""
Dashboard Metrics Generator
Generates dashboard metrics from fraud detection results for visualization
Supports PKR (Pakistani Rupees) currency
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Currency configuration
CURRENCY_CODE = "PKR"
CURRENCY_SYMBOL = "₨"


class DashboardGenerator:
    """Generates dashboard metrics from fraud detection results"""
    
    # Action thresholds (in PKR - Pakistani Rupees)
    BLOCK_AMOUNT_THRESHOLD = 2000000  # ₨2,000,000
    URGENT_REVIEW_AMOUNT_THRESHOLD = 500000  # ₨500,000
    CUSTOMER_CONTACT_AMOUNT_THRESHOLD = 200000  # ₨200,000
    
    BLOCK_TXN_COUNT_THRESHOLD = 10
    URGENT_REVIEW_TXN_COUNT_THRESHOLD = 5
    
    def __init__(self, results_df: pd.DataFrame):
        """
        Initialize dashboard generator
        
        Args:
            results_df: DataFrame with fraud detection results
        """
        self.results_df = results_df.copy()
        self.fraud_df = results_df[results_df['rule_based_fraud_detected'] == True].copy()
        logger.info(f"Dashboard generator initialized with {len(self.results_df)} total transactions, {len(self.fraud_df)} frauds")
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard metrics
        
        Returns:
            Dictionary with all dashboard data organized by category
        """
        logger.info("Generating dashboard metrics...")
        
        dashboard_data = {
            "summary": self._generate_summary_metrics(),
            "key_indicators": self._generate_key_indicators(),
            "actionable_alerts": self._generate_actionable_alerts(),
            "fraud_distribution": self._generate_fraud_distribution(),
            "top_accounts": self._generate_top_accounts(),
            "amount_distribution": self._generate_amount_distribution(),
            "temporal_analysis": self._generate_temporal_analysis(),
            "transaction_details": self._generate_transaction_details(),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_records_processed": len(self.results_df),
                "total_frauds_detected": len(self.fraud_df)
            }
        }
        
        logger.info("Dashboard metrics generation completed")
        return dashboard_data
    
    def _generate_summary_metrics(self) -> Dict[str, Any]:
        """Generate executive summary metrics"""
        
        total_transactions = len(self.results_df)
        fraudulent_transactions = len(self.fraud_df)
        fraud_percentage = (fraudulent_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        total_fraud_amount = self.fraud_df['transaction_amount'].sum()
        affected_accounts = self.fraud_df['account_number'].nunique()
        
        high_risk_accounts = self._get_high_risk_accounts_count()
        
        return {
            "total_transactions_analyzed": int(total_transactions),
            "fraudulent_transactions_detected": int(fraudulent_transactions),
            "fraud_percentage": round(fraud_percentage, 2),
            "total_fraud_amount": float(total_fraud_amount),
            "affected_accounts": int(affected_accounts),
            "high_risk_accounts": int(high_risk_accounts),
            "average_fraud_amount": float(self.fraud_df['transaction_amount'].mean()) if len(self.fraud_df) > 0 else 0,
            "max_fraud_amount": float(self.fraud_df['transaction_amount'].max()) if len(self.fraud_df) > 0 else 0
        }
    
    def _generate_key_indicators(self) -> Dict[str, Any]:
        """Generate key risk indicators"""
        
        fraud_severity_index = self._calculate_fraud_severity_index()
        accounts_requiring_action = self._get_accounts_requiring_action()
        new_beneficiary_fraud_rate = self._calculate_new_beneficiary_fraud_rate()
        
        return {
            "fraud_severity_index": round(fraud_severity_index, 2),
            "accounts_requiring_action": int(accounts_requiring_action),
            "new_beneficiary_fraud_rate": round(new_beneficiary_fraud_rate, 2),
            "risk_level": self._get_risk_level(fraud_severity_index),
            "action_urgency": self._get_action_urgency(accounts_requiring_action)
        }
    
    def _generate_actionable_alerts(self) -> Dict[str, Any]:
        """Generate actionable alerts prioritized for action"""
        
        # Add recommended actions
        fraud_with_actions = self.fraud_df.copy()
        fraud_with_actions['recommended_action'] = fraud_with_actions.apply(
            lambda row: self._get_recommended_action(row),
            axis=1
        )
        
        # Group by account
        account_summary = fraud_with_actions.groupby('account_number').agg({
            'transaction_amount': 'sum',
            'transaction_id': 'count',
            'rule_based_fraud_score': 'mean'
        }).reset_index()
        
        account_summary.columns = ['account_number', 'total_fraud_amount', 'fraud_transaction_count', 'avg_fraud_score']
        account_summary['risk_score'] = (account_summary['total_fraud_amount'] / 100000 + account_summary['fraud_transaction_count']) / 2
        account_summary['recommended_action'] = account_summary.apply(
            lambda row: self._get_recommended_action_by_account(row),
            axis=1
        )
        
        # Sort by fraud amount descending
        account_summary = account_summary.sort_values('total_fraud_amount', ascending=False)
        
        # Convert to list of dicts
        alerts = account_summary.head(20).to_dict('records')
        
        # Round numeric values
        for alert in alerts:
            alert['total_fraud_amount'] = round(alert['total_fraud_amount'], 2)
            alert['avg_fraud_score'] = round(alert['avg_fraud_score'], 2)
            alert['risk_score'] = round(alert['risk_score'], 2)
        
        return {
            "total_alerts": len(account_summary),
            "critical_alerts": len(account_summary[account_summary['recommended_action'] == 'BLOCK']),
            "urgent_alerts": len(account_summary[account_summary['recommended_action'] == 'URGENT_REVIEW']),
            "top_alerts": alerts
        }
    
    def _generate_fraud_distribution(self) -> Dict[str, Any]:
        """Generate fraud distribution analysis"""
        
        # By new beneficiary flag
        new_bene_fraud = len(self.fraud_df[self.fraud_df['New Beneficiary Flag'] == 1])
        repeat_bene_fraud = len(self.fraud_df[self.fraud_df['New Beneficiary Flag'] == 0])
        
        # By transaction type
        by_txn_type = self.fraud_df['transaction_type_code'].value_counts().to_dict()
        
        # By debit/credit
        by_cr_dr = self.fraud_df['cr_dr_ind'].value_counts().to_dict()
        
        return {
            "by_beneficiary_type": {
                "new_beneficiary": int(new_bene_fraud),
                "repeat_beneficiary": int(repeat_bene_fraud),
                "new_beneficiary_percentage": round(new_bene_fraud / len(self.fraud_df) * 100, 2) if len(self.fraud_df) > 0 else 0
            },
            "by_transaction_type": {str(k): int(v) for k, v in by_txn_type.items()},
            "by_debit_credit": {str(k): int(v) for k, v in by_cr_dr.items()}
        }
    
    def _generate_top_accounts(self) -> Dict[str, Any]:
        """Generate top affected accounts"""
        
        top_by_amount = self.fraud_df.groupby('account_number').agg({
            'transaction_amount': ['sum', 'count', 'mean'],
            'rule_based_fraud_score': 'mean'
        }).reset_index()
        
        top_by_amount.columns = ['account_number', 'total_fraud_amount', 'fraud_count', 'avg_transaction_amount', 'avg_fraud_score']
        top_by_amount = top_by_amount.sort_values('total_fraud_amount', ascending=False).head(10)
        
        accounts_list = []
        for idx, row in top_by_amount.iterrows():
            accounts_list.append({
                "rank": len(accounts_list) + 1,
                "account_number": row['account_number'],
                "total_fraud_amount": round(float(row['total_fraud_amount']), 2),
                "fraud_transaction_count": int(row['fraud_count']),
                "avg_transaction_amount": round(float(row['avg_transaction_amount']), 2),
                "avg_fraud_score": round(float(row['avg_fraud_score']), 2)
            })
        
        return {
            "top_10_accounts": accounts_list,
            "concentration_percentage": round((top_by_amount['total_fraud_amount'].sum() / self.fraud_df['transaction_amount'].sum() * 100), 2) if len(self.fraud_df) > 0 else 0
        }
    
    def _generate_amount_distribution(self) -> Dict[str, Any]:
        """Generate fraud amount distribution"""
        
        # Define amount ranges
        ranges = [
            (0, 1000, "0-1K"),
            (1000, 5000, "1K-5K"),
            (5000, 10000, "5K-10K"),
            (10000, 50000, "10K-50K"),
            (50000, float('inf'), "50K+")
        ]
        
        distribution = {}
        total_fraud_amount = 0
        
        for min_amt, max_amt, label in ranges:
            range_frauds = self.fraud_df[
                (self.fraud_df['transaction_amount'] >= min_amt) & 
                (self.fraud_df['transaction_amount'] < max_amt)
            ]
            count = len(range_frauds)
            amount = range_frauds['transaction_amount'].sum()
            distribution[label] = {
                "count": int(count),
                "amount": float(amount),
                "percentage": round(count / len(self.fraud_df) * 100, 2) if len(self.fraud_df) > 0 else 0
            }
            total_fraud_amount += amount
        
        return {
            "by_amount_range": distribution,
            "total_fraud_amount": float(total_fraud_amount)
        }
    
    def _generate_temporal_analysis(self) -> Dict[str, Any]:
        """Generate temporal patterns"""
        
        if len(self.fraud_df) == 0:
            return {"by_hour": {}, "by_day_of_week": {}, "note": "No fraud transactions"}
        
        # Parse timestamps
        self.fraud_df['transaction_datetime'] = pd.to_datetime(
            self.fraud_df['transaction_timestamp'],
            format='%d/%m/%Y %H:%M:%S',
            errors='coerce'
        )
        
        # By hour
        by_hour = self.fraud_df['transaction_datetime'].dt.hour.value_counts().sort_index().to_dict()
        by_hour_formatted = {str(int(k)): int(v) for k, v in by_hour.items()}
        
        # By day of week
        by_day = self.fraud_df['transaction_datetime'].dt.day_name().value_counts().to_dict()
        
        return {
            "by_hour": by_hour_formatted,
            "by_day_of_week": by_day,
            "peak_fraud_hour": int(max(by_hour.items(), key=lambda x: x[1])[0]) if by_hour else None
        }
    
    def _generate_transaction_details(self) -> Dict[str, Any]:
        """Generate detailed transaction information"""
        
        # Get top 50 frauds by score
        top_frauds = self.fraud_df.nlargest(50, 'rule_based_fraud_score')[
            ['account_number', 'transaction_id', 'transaction_timestamp', 'transaction_amount', 
             'New Beneficiary Flag', 'device_id', 'transaction_type_code', 'rule_based_fraud_score']
        ].copy()
        
        transactions = []
        for idx, row in top_frauds.iterrows():
            transactions.append({
                "account_number": row['account_number'],
                "transaction_id": row['transaction_id'],
                "timestamp": row['transaction_timestamp'],
                "amount": float(row['transaction_amount']),
                "new_beneficiary": bool(row['New Beneficiary Flag']),
                "device_id": row['device_id'],
                "transaction_type_code": row['transaction_type_code'],
                "fraud_score": float(row['rule_based_fraud_score']),
                "risk_level": self._get_transaction_risk_level(row['rule_based_fraud_score'])
            })
        
        return {
            "total_high_risk_transactions": len(top_frauds),
            "sample_transactions": transactions
        }
    
    # Helper methods
    
    def _calculate_fraud_severity_index(self) -> float:
        """Calculate fraud severity score (0-100)"""
        if len(self.fraud_df) == 0:
            return 0
        
        # Weighted calculation
        amount_weight = (self.fraud_df['transaction_amount'].sum() / 1000000) * 30  # 30% weight
        count_weight = (len(self.fraud_df) / 1000) * 30  # 30% weight
        score_weight = (self.fraud_df['rule_based_fraud_score'].mean() / 10) * 40  # 40% weight
        
        severity = min(100, amount_weight + count_weight + score_weight)
        return severity
    
    def _get_high_risk_accounts_count(self) -> int:
        """Count accounts with fraud amount > 5K"""
        high_risk = self.fraud_df.groupby('account_number')['transaction_amount'].sum()
        return len(high_risk[high_risk > self.CUSTOMER_CONTACT_AMOUNT_THRESHOLD])
    
    def _calculate_new_beneficiary_fraud_rate(self) -> float:
        """Calculate % of frauds involving new beneficiaries"""
        if len(self.fraud_df) == 0:
            return 0
        return (self.fraud_df['New Beneficiary Flag'] == 1).sum() / len(self.fraud_df) * 100
    
    def _get_accounts_requiring_action(self) -> int:
        """Count accounts requiring some action"""
        account_totals = self.fraud_df.groupby('account_number')['transaction_amount'].sum()
        return len(account_totals[account_totals >= self.CUSTOMER_CONTACT_AMOUNT_THRESHOLD])
    
    def _get_recommended_action(self, row) -> str:
        """Get recommended action for a transaction"""
        amount = row['transaction_amount']
        if amount >= self.BLOCK_AMOUNT_THRESHOLD:
            return "BLOCK"
        elif amount >= self.URGENT_REVIEW_AMOUNT_THRESHOLD:
            return "URGENT_REVIEW"
        elif amount >= self.CUSTOMER_CONTACT_AMOUNT_THRESHOLD:
            return "CONTACT_CUSTOMER"
        else:
            return "MONITOR"
    
    def _get_recommended_action_by_account(self, row) -> str:
        """Get recommended action for an account"""
        amount = row['total_fraud_amount']
        count = row['fraud_transaction_count']
        
        if amount >= self.BLOCK_AMOUNT_THRESHOLD or count >= self.BLOCK_TXN_COUNT_THRESHOLD:
            return "BLOCK"
        elif amount >= self.URGENT_REVIEW_AMOUNT_THRESHOLD or count >= self.URGENT_REVIEW_TXN_COUNT_THRESHOLD:
            return "URGENT_REVIEW"
        elif amount >= self.CUSTOMER_CONTACT_AMOUNT_THRESHOLD:
            return "CONTACT_CUSTOMER"
        else:
            return "MONITOR"
    
    def _get_risk_level(self, severity_index: float) -> str:
        """Get risk level based on severity index"""
        if severity_index >= 75:
            return "CRITICAL"
        elif severity_index >= 50:
            return "HIGH"
        elif severity_index >= 25:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_action_urgency(self, accounts_requiring_action: int) -> str:
        """Get urgency of action required"""
        if accounts_requiring_action >= 10:
            return "IMMEDIATE"
        elif accounts_requiring_action >= 5:
            return "HIGH"
        elif accounts_requiring_action > 0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_transaction_risk_level(self, fraud_score: float) -> str:
        """Get risk level for a transaction"""
        if fraud_score >= 8:
            return "CRITICAL"
        elif fraud_score >= 6:
            return "HIGH"
        elif fraud_score >= 4:
            return "MEDIUM"
        else:
            return "LOW"
