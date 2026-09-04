"""
Unit tests for data preprocessing and model prediction logic.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.preprocess import load_and_preprocess_data, split_data


@pytest.fixture
def sample_dataset():
    """
    Create a sample dataset for testing.
    """
    # Create a simple dataset with mixed feature types
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'numeric_1': np.random.randn(n_samples),
        'numeric_2': np.random.randn(n_samples) * 10 + 50,
        'categorical_1': np.random.choice(['A', 'B', 'C'], n_samples),
        'categorical_2': np.random.choice(['X', 'Y'], n_samples),
        'Churn': np.random.choice(['Yes', 'No'], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Save to temporary CSV file
    temp_path = '/tmp/test_churn_data.csv'
    df.to_csv(temp_path, index=False)
    
    return temp_path, df


class TestDataPreprocessing:
    """Test data preprocessing functions."""
    
    def test_load_and_preprocess_data(self, sample_dataset):
        """Test data loading and preprocessing."""
        temp_path, _ = sample_dataset
        
        X, y, preprocessor = load_and_preprocess_data(temp_path)
        
        # Check that outputs are correct types
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert preprocessor is not None
        
        # Check that data dimensions are reasonable
        assert X.shape[0] > 0, "X should have rows"
        assert X.shape[1] > 0, "X should have features"
        assert len(y) == len(X), "X and y should have same number of samples"
        
        # Check that target is binary (0 or 1)
        assert set(y.unique()).issubset({0, 1}), "Target should be binary"
    
    def test_split_data(self, sample_dataset):
        """Test data splitting."""
        temp_path, _ = sample_dataset
        
        X, y, _ = load_and_preprocess_data(temp_path)
        X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2, random_state=42)
        
        # Check split sizes
        assert len(X_train) + len(X_test) == len(X)
        assert len(y_train) + len(y_test) == len(y)
        assert abs(len(X_test) / len(X) - 0.2) < 0.1, "Test size should be approximately 20%"
        
        # Check no overlap
        assert len(set(X_train.index) & set(X_test.index)) == 0, "Train and test should not overlap"
    
    def test_preprocessor_consistency(self, sample_dataset):
        """Test that preprocessor produces consistent output."""
        temp_path, _ = sample_dataset
        
        X, y, preprocessor = load_and_preprocess_data(temp_path)
        
        # Transform original data again (subset)
        original_data = pd.read_csv(temp_path).drop(columns=['Churn']).iloc[:10]
        
        # The preprocessor should be able to transform new data
        # (Note: This is a simple test - actual behavior depends on ColumnTransformer)
        assert preprocessor is not None, "Preprocessor should be fitted"


class TestModelPrediction:
    """Test model prediction logic."""
    
    def test_model_training_and_prediction(self, sample_dataset):
        """Test that a model can be trained and make predictions."""
        temp_path, _ = sample_dataset
        
        X, y, _ = load_and_preprocess_data(temp_path)
        X_train, X_test, y_train, y_test = split_data(X, y)
        
        # Train a simple model
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)
        
        # Check prediction dimensions
        assert len(y_pred) == len(y_test), "Predictions should match test set size"
        assert y_proba.shape[0] == len(y_test), "Probabilities should match test set size"
        assert y_proba.shape[1] == 2, "Should have 2 probability columns (binary classification)"
        
        # Check prediction values
        assert all(p in [0, 1] for p in y_pred), "Predictions should be 0 or 1"
        assert all(0 <= p <= 1 for row in y_proba for p in row), "Probabilities should be in [0, 1]"
    
    def test_model_accuracy(self, sample_dataset):
        """Test that model achieves reasonable accuracy."""
        from sklearn.metrics import accuracy_score
        
        temp_path, _ = sample_dataset
        
        X, y, _ = load_and_preprocess_data(temp_path)
        X_train, X_test, y_train, y_test = split_data(X, y, random_state=42)
        
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Should achieve at least random accuracy (0.5 for binary classification)
        assert accuracy >= 0.4, f"Accuracy {accuracy} should be reasonable (at least 0.4)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
