"""
FastAPI application for real-time customer churn prediction.
"""

import os
import sys
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
import mlflow
import mlflow.pyfunc
import mlflow.tracking
from pydantic import ValidationError
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Pydantic models
from src.api.models import ChurnPredictionRequest, ChurnPredictionResponse, HealthCheckResponse

# Global variables for model and metadata
MODEL = None
MODEL_VERSION = "unknown"
MODEL_LOADED = False
MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "ChurnPredictionModel")
MODEL_STAGE = os.getenv("MLFLOW_MODEL_STAGE", "Production")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")


def normalize_raw_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """Convert numeric strings from CSV clients to numeric model inputs."""
    normalized = {}
    for name, value in features.items():
        if isinstance(value, str):
            stripped_value = value.strip()
            try:
                normalized[name] = float(stripped_value) if "." in stripped_value else int(stripped_value)
                continue
            except ValueError:
                pass
        normalized[name] = value
    return normalized


def get_model_input_columns() -> list[str]:
    """Return the deployed model's named input columns when available."""
    try:
        schema = MODEL.metadata.get_input_schema()
        columns = schema.input_names()
        if isinstance(columns, list) and all(isinstance(column, str) for column in columns):
            return columns
    except Exception:
        pass
    return []


async def load_model_on_startup():
    """
    Load the latest Production stage model from MLflow Model Registry.
    Called on application startup.
    """
    global MODEL, MODEL_VERSION, MODEL_LOADED
    
    try:
        logger.info(f"Attempting to load model: {MODEL_NAME}/{MODEL_STAGE} from {MLFLOW_TRACKING_URI}")
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        
        # Try to load the model from MLflow Model Registry
        model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
        logger.info(f"Loading model from URI: {model_uri}")
        
        MODEL = mlflow.pyfunc.load_model(model_uri)
        
        # Get model version info
        try:
            client = mlflow.tracking.MlflowClient()
            version_info = client.get_latest_versions(MODEL_NAME, stages=[MODEL_STAGE])
            if version_info:
                MODEL_VERSION = str(version_info[0].version)
                MODEL_LOADED = True
                logger.info(f"✓ Successfully loaded model {MODEL_NAME} version {MODEL_VERSION} (Stage: {MODEL_STAGE})")
            else:
                logger.warning(f"No model found for {MODEL_NAME} in stage {MODEL_STAGE}. API will return 503 for /predict.")
                MODEL_LOADED = False
        except Exception as e:
            logger.error(f"Error retrieving model version info: {e}")
            MODEL_LOADED = True  # Model loaded but version unknown
            
    except Exception as e:
        logger.error(f"Error loading model from MLflow: {e}")
        logger.info("API will start but /predict endpoint will return 503 Service Unavailable.")
        MODEL = None
        MODEL_LOADED = False


async def shutdown_model():
    """
    Cleanup on application shutdown.
    """
    global MODEL
    logger.info("Shutting down API...")
    MODEL = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifespan of the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    await load_model_on_startup()
    yield
    # Shutdown
    await shutdown_model()


# Initialize FastAPI app
app = FastAPI(
    title="Churn Prediction API",
    description="Real-time API for predicting customer churn using a scikit-learn model managed by MLflow.",
    version="1.0.0",
    lifespan=lifespan
)


@app.get(
    "/health",
    summary="Health check endpoint",
    response_model=HealthCheckResponse,
    tags=["Health"]
)
async def health_check() -> HealthCheckResponse:
    """
    Check the health of the API and model availability.
    
    Returns:
        - 200 OK if the API is running and the model is loaded
        - 503 Service Unavailable if the model is not loaded
    """
    if MODEL_LOADED and MODEL is not None:
        return HealthCheckResponse(
            status="ok",
            model_status="loaded",
            model_version=MODEL_VERSION
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded or unavailable. Check MLflow connection and model registry."
        )


@app.post(
    "/predict",
    response_model=ChurnPredictionResponse,
    summary="Predict customer churn",
    tags=["Prediction"]
)
async def predict_churn(request: ChurnPredictionRequest) -> ChurnPredictionResponse:
    """
    Predict customer churn based on provided features.
    
    Args:
        request: ChurnPredictionRequest containing customer features
        
    Returns:
        - 200 OK with prediction, probability, and model version
        - 400 Bad Request if input validation fails
        - 503 Service Unavailable if model is not loaded
        - 500 Internal Server Error if prediction fails
    """
    # Check if model is loaded
    if MODEL is None or not MODEL_LOADED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model is not available. Please check the API logs."
        )
    
    try:
        # Convert request to DataFrame for model inference
        if isinstance(request.features, dict):
            normalized_features = normalize_raw_features(request.features)
            model_columns = get_model_input_columns()
            if model_columns:
                missing_columns = [column for column in model_columns if column not in normalized_features]
                if missing_columns:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required model features: {missing_columns}"
                    )
                normalized_features = {
                    column: normalized_features[column] for column in model_columns
                }
            input_data = pd.DataFrame([normalized_features])
        else:
            if get_model_input_columns():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This deployed model requires named raw features. Send a JSON object with feature names."
                )
            input_data = pd.DataFrame([request.features])
        
        logger.info(f"Making prediction with input shape: {input_data.shape}")
        
        # Make prediction
        prediction = MODEL.predict(input_data)[0]
        
        # Try to get probability
        probability = 0.0
        try:
            # Try predict_proba method
            if hasattr(MODEL, 'predict_proba'):
                proba_array = MODEL.predict_proba(input_data)
                if isinstance(proba_array, np.ndarray) and proba_array.shape[1] > 1:
                    probability = float(proba_array[0, 1])
                else:
                    probability = float(prediction)
            else:
                # For MLflow pyfunc, try alternative method
                probability = float(prediction)
        except Exception as e:
            logger.warning(f"Could not compute probability: {e}. Using prediction as fallback.")
            probability = float(prediction)
        
        logger.info(f"Prediction result - class: {int(prediction)}, probability: {probability:.4f}")
        
        return ChurnPredictionResponse(
            prediction=int(prediction),
            probability=float(probability),
            model_version=MODEL_VERSION
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Value error during prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input values: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed due to an internal server error: {str(e)}"
        )


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint with API information.
    """
    return {
        "message": "Churn Prediction API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
