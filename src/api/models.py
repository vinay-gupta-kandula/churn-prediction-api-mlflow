"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Any, Dict, List, Union


class ChurnPredictionRequest(BaseModel):
    """
    Request model for churn prediction.
    
    Note: Feature names and counts depend on the dataset's preprocessing.
    This example uses common Telco Customer Churn dataset features.
    For actual deployment, adapt feature names to your preprocessed dataset.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "features": {
                "gender": "Female",
                "SeniorCitizen": 0,
                "Partner": "Yes",
                "Dependents": "No",
                "tenure": 1,
                "PhoneService": "No",
                "MultipleLines": "No phone service",
                "InternetService": "DSL",
                "OnlineSecurity": "No",
                "OnlineBackup": "Yes",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "No",
                "StreamingMovies": "No",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 29.85
            }
        }
    })

    features: Union[List[float], Dict[str, Any]] = Field(
        ...,
        description="Raw customer feature object for a trained model, or a numeric feature list for compatible models."
    )

    @model_validator(mode="before")
    @classmethod
    def accept_raw_feature_object(cls, value: Any) -> Any:
        """Allow callers to post a raw CSV row without an extra envelope."""
        if isinstance(value, dict) and value and "features" not in value:
            return {"features": value}
        return value

class ChurnPredictionResponse(BaseModel):
    """
    Response model for churn prediction results.
    """
    prediction: int = Field(
        ...,
        description="Predicted churn label (0: No Churn, 1: Churn)"
    )
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability of churn (class 1) prediction"
    )
    model_version: str = Field(
        ...,
        description="Version of the model used for prediction from MLflow Registry"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "prediction": 1,
            "probability": 0.75,
            "model_version": "1"
        }
    })


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoint.
    """
    status: str = Field(..., description="Overall API status")
    model_status: str = Field(..., description="Model loading status")
    model_version: str = Field(..., description="Version of the loaded model")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "ok",
            "model_status": "loaded",
            "model_version": "1"
        }
    })
