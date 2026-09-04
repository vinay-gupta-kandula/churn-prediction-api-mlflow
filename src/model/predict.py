"""
Prediction utility for making predictions using the trained model.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Any


def make_prediction(
    model: Any,
    input_data: pd.DataFrame
) -> Tuple[int, float]:
    """
    Make a churn prediction using the loaded model.
    
    Args:
        model: Trained scikit-learn model or MLflow pyfunc model.
        input_data: Preprocessed input features as DataFrame.
        
    Returns:
        Tuple of (predicted_class, probability_of_churn)
    """
    # Get prediction
    prediction = model.predict(input_data)[0]
    
    # Get probability if available
    if hasattr(model, 'predict_proba'):
        probability = model.predict_proba(input_data)[0, 1]
    else:
        # For MLflow pyfunc model, try to extract probability
        try:
            proba_output = model.predict_proba(input_data)
            if isinstance(proba_output, np.ndarray):
                probability = proba_output[0, 1] if proba_output.shape[1] > 1 else float(prediction)
            else:
                probability = float(prediction)
        except Exception:
            probability = float(prediction)
    
    return int(prediction), float(probability)
