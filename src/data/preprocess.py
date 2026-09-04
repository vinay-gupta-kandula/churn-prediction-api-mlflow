"""
Data loading and preprocessing utilities for customer churn prediction.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from typing import Tuple, Any
import os


def load_raw_data(filepath: str) -> Tuple[pd.DataFrame, pd.Series, Any]:
    """Load the dataset and create the fitted feature preprocessor."""
    df = pd.read_csv(filepath)
    df = df.ffill().bfill().dropna()

    if 'Churn' in df.columns:
        y = (df['Churn'] == 'Yes').astype(int)
        X = df.drop(columns=['Churn'])
    else:
        y = (df.iloc[:, -1] == 'Yes').astype(int) if df.iloc[0, -1] in ['Yes', 'No'] else df.iloc[:, -1].astype(int)
        X = df.iloc[:, :-1]

    columns_to_drop = [
        col for col in X.columns
        if X[col].dtype == 'object' and X[col].nunique() > 50
    ]
    X = X.drop(columns=columns_to_drop)

    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X.select_dtypes(include=['object']).columns.tolist()
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='drop'
    )
    preprocessor.fit(X)
    return X, y, preprocessor


def load_and_preprocess_data(filepath: str) -> Tuple[pd.DataFrame, pd.Series, Any]:
    """
    Load and preprocess the customer churn dataset.
    
    Args:
        filepath: Path to the CSV dataset file.
        
    Returns:
        Tuple containing:
        - X: Preprocessed features (DataFrame)
        - y: Target variable (Series)
        - preprocessor: Fitted ColumnTransformer for consistent inference preprocessing
    """
    X_raw, y, preprocessor = load_raw_data(filepath)
    X_processed = preprocessor.transform(X_raw)
    X_processed = pd.DataFrame(X_processed)
    
    return X_processed, y, preprocessor


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split preprocessed data into training and testing sets.
    
    Args:
        X: Preprocessed features.
        y: Target variable.
        test_size: Proportion of data to use for testing (default: 0.2).
        random_state: Random seed for reproducibility (default: 42).
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    from sklearn.model_selection import train_test_split
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    return X_train, X_test, y_train, y_test
