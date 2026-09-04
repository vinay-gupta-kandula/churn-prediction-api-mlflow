"""
Model training script with MLflow integration for experiment tracking.
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import mlflow
import mlflow.sklearn
from typing import Tuple, Any
import subprocess
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.preprocess import load_raw_data, split_data


def get_git_commit_hash() -> str:
    """
    Get the current Git commit hash for reproducibility tracking.
    
    Returns:
        Git commit hash or "unknown" if not in a git repository.
    """
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
        return commit_hash
    except Exception:
        return "unknown"


def train_model(
    data_path: str,
    model_name: str = "ChurnPredictionModel",
    experiment_name: str = "Churn Prediction",
) -> Tuple[str, float]:
    """
    Train a logistic regression model with MLflow experiment tracking.
    
    Args:
        data_path: Path to the training dataset CSV file.
        model_name: Name to register the model under in MLflow Model Registry.
        experiment_name: Name of the MLflow experiment.
        
    Returns:
        Tuple of (model_version, f1_score) for the trained model.
    """
    # Set MLflow tracking URI from environment variable
    mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://127.0.0.1:5000')
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    
    # Set or create experiment
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id
    except Exception as e:
        print(f"Warning: Could not set MLflow experiment: {e}")
        experiment_id = None
    
    print(f"Training model with MLflow tracking URI: {mlflow_tracking_uri}")
    
    # Load and preprocess data
    print(f"Loading data from {data_path}...")
    X, y, preprocessor = load_raw_data(data_path)
    
    # Split raw data so the fitted preprocessor is part of the deployed model.
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2, random_state=42)
    
    print(f"Data shapes - X_train: {X_train.shape}, X_test: {X_test.shape}")
    
    # Start MLflow run
    with mlflow.start_run(experiment_id=experiment_id):
        # Define model hyperparameters
        model_params = {
            'solver': 'lbfgs',
            'max_iter': 1000,
            'random_state': 42,
            'class_weight': 'balanced'
        }
        
        # Log hyperparameters
        for param_name, param_value in model_params.items():
            mlflow.log_param(param_name, param_value)
        
        # Train model
        print("Training Logistic Regression model...")
        from sklearn.pipeline import Pipeline

        model = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', LogisticRegression(**model_params))
        ])
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred)
        }
        
        # Log metrics
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)
        
        print(f"Model metrics: {metrics}")
        
        # Log Git commit hash
        git_commit = get_git_commit_hash()
        mlflow.log_param('git_commit', git_commit)
        
        # Log preprocessing info
        mlflow.log_text(
            f"Preprocessor: ColumnTransformer with StandardScaler and OneHotEncoder\n"
            f"Raw feature count: {X_train.shape[1]}\n"
            f"Categorical features encoded: Yes",
            artifact_file="preprocessing_info.txt"
        )
        
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name=model_name,
            input_example=X_test.iloc[:1],
            await_registration_for=300
        )
        
        print(f"Model logged to MLflow")
        
        # Get the latest version
        client = mlflow.tracking.MlflowClient()
        try:
            versions = client.get_latest_versions(model_name, stages=["None"])
            latest_version = max(versions, key=lambda v: int(v.version))
            
            # Transition to Production stage
            print(f"Transitioning model version {latest_version.version} to Production stage...")
            client.transition_model_version_stage(
                name=model_name,
                version=latest_version.version,
                stage="Production"
            )
            
            return latest_version.version, metrics['f1_score']
        except Exception as e:
            print(f"Warning: Could not transition model to Production: {e}")
            return "1", metrics['f1_score']


if __name__ == "__main__":
    # Example: train_model with local dataset
    # You would need to download the Telco Customer Churn dataset first
    
    # Check if dataset exists
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'WA_Fn-UseC_-Telco-Customer-Churn.csv')
    
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        print("Please download the Telco Customer Churn dataset from Kaggle:")
        print("https://www.kaggle.com/datasets/blastchar/telco-customer-churn")
        sys.exit(1)
    
    model_version, f1 = train_model(data_path)
    print(f"\n✓ Model training complete!")
    print(f"  Model Version: {model_version}")
    print(f"  F1-Score: {f1:.4f}")
