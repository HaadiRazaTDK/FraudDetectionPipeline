"""
Test Script for UBL Fraud Detection API
This script tests both API endpoints with sample data
"""
import requests
import os
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200

def test_generate_rules(csv_file: str, input_date: str):
    """Test rules generation endpoint"""
    print("\n" + "="*60)
    print("Testing Rules Generation Endpoint")
    print("="*60)
    
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found!")
        return False
    
    with open(csv_file, 'rb') as f:
        files = {'file': f}
        data = {'input_date': input_date}
        
        print(f"Uploading file: {csv_file}")
        print(f"Input date: {input_date}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/generate-rules",
            files=files,
            data=data
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response:")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        print(f"  Rules File: {result['rules_file']}")
        print(f"  Accounts Processed: {result['accounts_processed']}")
        print(f"  Date Range: {result['date_range']['start']} to {result['date_range']['end']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_list_rules():
    """Test list rules endpoint"""
    print("\n" + "="*60)
    print("Testing List Rules Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/v1/rules/list")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total Rules Files: {result['total_files']}")
        
        if result['rules_files']:
            print("\nAvailable Rules Files:")
            for rule_file in result['rules_files']:
                print(f"  - {rule_file['filename']} (Date: {rule_file['date']}, Size: {rule_file['size_kb']} KB)")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_detect_fraud(csv_file: str, detection_date: str, rules_date: str, output_file: str = "test_fraud_results.csv"):
    """Test fraud detection endpoint"""
    print("\n" + "="*60)
    print("Testing Fraud Detection Endpoint")
    print("="*60)
    
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found!")
        return False
    
    with open(csv_file, 'rb') as f:
        files = {'file': f}
        data = {
            'detection_date': detection_date,
            'rules_date': rules_date
        }
        
        print(f"Uploading file: {csv_file}")
        print(f"Detection date: {detection_date}")
        print(f"Rules date: {rules_date}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/detect-fraud",
            files=files,
            data=data
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        # Save the CSV response
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"Success! Results saved to: {output_file}")
        
        # Read and display summary
        import pandas as pd
        results_df = pd.read_csv(output_file)
        
        print(f"\nResults Summary:")
        print(f"  Total Transactions: {len(results_df)}")
        print(f"  Fraudulent Transactions: {results_df['rule_based_fraud_detected'].sum()}")
        print(f"  Fraud Rate: {(results_df['rule_based_fraud_detected'].sum() / len(results_df) * 100):.2f}%")
        
        if results_df['rule_based_fraud_detected'].sum() > 0:
            print(f"\nFraud Score Distribution:")
            print(results_df[results_df['rule_based_fraud_detected'] == True]['rule_based_fraud_score'].value_counts().sort_index())
            
            print(f"\nMost Triggered Rules:")
            rule_columns = [
                'fraud_device_change',
                'fraud_daily_debit_count',
                'fraud_daily_debit_amt',
                'fraud_txn_amt',
                'fraud_hourly_count',
                'fraud_new_bene_high_transaction',
                'fraud_unusual_hour',
                'fraud_device_change_new_bene_bb_75k'
            ]
            for rule in rule_columns:
                if rule in results_df.columns:
                    count = results_df[rule].sum()
                    print(f"  {rule}: {count}")
        
        return True
    else:
        print(f"Error: {response.text}")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*60)
    print("UBL FRAUD DETECTION API - TEST SUITE")
    print("="*60)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Health check failed! Make sure the server is running.")
        return
    
    print("\n✅ Health check passed!")
    
    # Generate sample data if not exists
    sample_file = "sample_transactions.csv"
    if not os.path.exists(sample_file):
        print(f"\n⚠️  Sample data file not found. Generating...")
        os.system("python generate_sample_data.py")
    
    # Test 2: Generate rules
    input_date = "31/12/2023"  # Use a date that has 3 months of history in sample data
    if test_generate_rules(sample_file, input_date):
        print("\n✅ Rules generation passed!")
    else:
        print("\n❌ Rules generation failed!")
        return
    
    # Test 3: List rules
    if test_list_rules():
        print("\n✅ List rules passed!")
    else:
        print("\n❌ List rules failed!")
    
    # Test 4: Detect fraud
    detection_date = "01/01/2024"
    rules_date = "31/12/2023"
    if test_detect_fraud(sample_file, detection_date, rules_date):
        print("\n✅ Fraud detection passed!")
    else:
        print("\n❌ Fraud detection failed!")
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "health":
            test_health_check()
        elif command == "generate":
            csv_file = sys.argv[2] if len(sys.argv) > 2 else "sample_transactions.csv"
            input_date = sys.argv[3] if len(sys.argv) > 3 else "31/12/2023"
            test_generate_rules(csv_file, input_date)
        elif command == "list":
            test_list_rules()
        elif command == "detect":
            csv_file = sys.argv[2] if len(sys.argv) > 2 else "sample_transactions.csv"
            detection_date = sys.argv[3] if len(sys.argv) > 3 else "01/01/2024"
            rules_date = sys.argv[4] if len(sys.argv) > 4 else "31/12/2023"
            test_detect_fraud(csv_file, detection_date, rules_date)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python test_api.py [health|generate|list|detect|all]")
    else:
        run_all_tests()
