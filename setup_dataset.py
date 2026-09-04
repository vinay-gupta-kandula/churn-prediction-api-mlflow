#!/usr/bin/env python
"""
Dataset setup helper for Telco Customer Churn dataset.

This script provides instructions and utilities for downloading and preparing
the Telco Customer Churn dataset for the churn prediction model.

Usage:
    python setup_dataset.py
"""

import os
import sys
from pathlib import Path


def print_instructions():
    """Print dataset setup instructions."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║          CHURN PREDICTION API - DATASET SETUP INSTRUCTIONS                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

DATASET: Telco Customer Churn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Dataset Information:
  • Name: Telco Customer Churn
  • Source: Kaggle (https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
  • Records: ~7,043 customers
  • Features: ~20 attributes (demographics, account, services)
  • Target: Binary (Churn: Yes/No)

📥 DOWNLOAD INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Option 1: Manual Download (Recommended for quick setup)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Go to: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
2. Click "Download" button (requires Kaggle account)
3. Extract the ZIP file to get: WA_Fn-UseC_-Telco-Customer-Churn.csv
4. Place the CSV in the 'data/' directory of this project:
   
   churn-prediction-api-mlflow/
   └── data/
       └── WA_Fn-UseC_-Telco-Customer-Churn.csv  ← Place it here

Option 2: Using Kaggle API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Requires: kaggle Python package and API credentials

  # Install Kaggle package
  pip install kaggle
  
  # Set up Kaggle API credentials
  # Follow: https://github.com/Kaggle/kaggle-api#credentials
  # (Create ~/.kaggle/kaggle.json with your API token)
  
  # Download dataset
  kaggle datasets download -d blastchar/telco-customer-churn
  
  # Extract to data/ directory
  unzip telco-customer-churn.zip -d data/

📁 Project Structure After Download:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

churn-prediction-api-mlflow/
├── src/
│   ├── api/
│   ├── data/
│   └── model/
├── tests/
├── data/                           ← Dataset goes here
│   └── WA_Fn-UseC_-Telco-Customer-Churn.csv
├── Dockerfile.api
├── Dockerfile.mlflow
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── ARCHITECTURE.md

✅ VERIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After placing the CSV file, verify:

  # Check file exists
  ls data/WA_Fn-UseC_-Telco-Customer-Churn.csv
  
  # Check file size (should be ~500KB+)
  ls -lh data/WA_Fn-UseC_-Telco-Customer-Churn.csv
  
  # Verify CSV structure (first few rows)
  head -5 data/WA_Fn-UseC_-Telco-Customer-Churn.csv

🚀 NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Start the Docker stack:
   docker-compose up -d
   
2. Train the model:
   docker-compose run --rm api python -m src.model.train
   
3. Make predictions:
   curl -X POST http://localhost:8000/predict \\
     -H "Content-Type: application/json" \\
     -d '{"features": [0.1, 0.2, ...]}'
   
4. View MLflow UI:
   Open: http://localhost:5000

📚 ADDITIONAL RESOURCES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Dataset Details: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
• Kaggle Account: https://www.kaggle.com
• Kaggle API Docs: https://github.com/Kaggle/kaggle-api
• Project README: ./README.md
• Architecture Guide: ./ARCHITECTURE.md

════════════════════════════════════════════════════════════════════════════════
    """)


def check_data_directory():
    """Check if data directory exists and contains the dataset."""
    data_dir = Path("data")
    expected_file = data_dir / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    
    print("\n📁 Checking data directory...")
    
    if not data_dir.exists():
        print(f"  ✗ Data directory does not exist: {data_dir}")
        print(f"  → Creating directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {data_dir}")
        return False
    
    print(f"  ✓ Data directory exists: {data_dir}")
    
    if expected_file.exists():
        file_size = expected_file.stat().st_size
        print(f"  ✓ Dataset found: {expected_file}")
        print(f"    Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        return True
    else:
        print(f"  ✗ Dataset not found: {expected_file}")
        return False


def main():
    """Main setup function."""
    print_instructions()
    
    if check_data_directory():
        print("\n✅ Data directory is ready! You can now:")
        print("   • Run: docker-compose up")
        print("   • Or:  python -m src.model.train")
    else:
        print("\n⚠️  Please download the dataset first:")
        print("   1. Visit: https://www.kaggle.com/datasets/blastchar/telco-customer-churn")
        print("   2. Download: WA_Fn-UseC_-Telco-Customer-Churn.csv")
        print("   3. Place in: data/ directory")
        print("   4. Re-run this script to verify")
        sys.exit(1)


if __name__ == "__main__":
    main()
