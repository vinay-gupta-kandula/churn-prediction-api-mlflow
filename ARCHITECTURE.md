# Project Architecture

## System Overview

This document provides a detailed architectural overview of the Churn Prediction API system, including component interactions, data flows, and design patterns.

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│                   (Web/Mobile/Services)                          │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  • Request Validation (Pydantic)                         │   │
│  │  • Error Handling (HTTPException)                        │   │
│  │  • Response Formatting                                   │   │
│  │  • Health Checks                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────┬──────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Inference Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Loaded Model (from MLflow)                              │   │
│  │  • predict(features) → class label                       │   │
│  │  • predict_proba(features) → probabilities               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────┬──────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│              MLflow Model Registry & Tracking                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  • Model Versioning (v1, v2, v3, ...)                   │   │
│  │  • Stage Management (Staging, Production, ...)           │   │
│  │  • Experiment History                                    │   │
│  │  • Metrics & Parameters Tracking                         │   │
│  │  • Artifact Storage                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────┬──────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Persistent Storage                             │
│  • SQLite Database (mlruns.db) - Backend store                  │
│  • File System - Artifact storage (trained models, etc.)         │
└──────────────────────────────────────────────────────────────────┘
```

## 2. Component Architecture

### 2.1 Data Preparation Component

**File**: `src/data/preprocess.py`

**Responsibilities**:
- Load raw CSV dataset
- Handle missing values (forward fill, backward fill, drop)
- Identify numeric and categorical features
- Apply feature transformations:
  - Numeric: StandardScaler (z-score normalization)
  - Categorical: OneHotEncoder (create binary columns)
- Return preprocessed features (X), target (y), and fitted preprocessor

**Key Functions**:
```python
def load_and_preprocess_data(filepath: str) -> Tuple[pd.DataFrame, pd.Series, Any]
def split_data(X, y, test_size=0.2, random_state=42) -> Tuple[...]
```

**Design Decisions**:
- **ColumnTransformer**: Allows parallel processing of numeric and categorical features
- **StandardScaler**: Centers data (mean=0) and scales by standard deviation
- **OneHotEncoder**: Converts categorical strings to binary indicators
- **Stratified Split**: Maintains class distribution in train/test sets

### 2.2 Model Training Component

**File**: `src/model/train.py`

**Responsibilities**:
- Load and preprocess training data
- Train scikit-learn model (Logistic Regression)
- Evaluate model on test set
- Log experiments, metrics, and parameters to MLflow
- Register trained model in MLflow Model Registry
- Transition model to Production stage

**Workflow**:
```
1. Connect to MLflow tracking server
2. Start experiment run
3. Load & preprocess data
4. Split into train/test sets
5. Train Logistic Regression model
6. Evaluate on test set
   ├─ Accuracy
   ├─ Precision
   ├─ Recall
   └─ F1-Score
7. Log to MLflow:
   ├─ Hyperparameters (solver, max_iter, C, etc.)
   ├─ Metrics (accuracy, precision, recall, f1_score)
   ├─ Model artifact (sklearn model object)
   └─ Git commit hash (for reproducibility)
8. Register model as "ChurnPredictionModel"
9. Transition to "Production" stage
```

**MLflow Integration**:
```python
mlflow.start_run()
  mlflow.log_param("solver", "lbfgs")
  mlflow.log_metric("accuracy", 0.87)
  mlflow.sklearn.log_model(model, "model", registered_model_name="ChurnPredictionModel")
mlflow.end_run()

# Later: Transition version N to Production
client.transition_model_version_stage(
    name="ChurnPredictionModel",
    version="1",
    stage="Production"
)
```

### 2.3 Prediction Utility Component

**File**: `src/model/predict.py`

**Responsibilities**:
- Wrapper function for making predictions
- Extract prediction class and probability
- Handle different model types (sklearn, MLflow pyfunc)

**Function**:
```python
def make_prediction(model, input_data) -> Tuple[int, float]
```

### 2.4 API Layer Component

**File**: `src/api/main.py`

**Responsibilities**:
- Initialize FastAPI application
- Load model on startup from MLflow
- Implement /health endpoint (model status)
- Implement /predict endpoint (make predictions)
- Validate requests with Pydantic models
- Handle errors with appropriate HTTP status codes
- Provide auto-generated API documentation (Swagger UI)

**Endpoints**:

1. **GET /health**
   - Status: 200 (OK) | 503 (Service Unavailable)
   - Response: JSON with model status and version

2. **POST /predict**
   - Status: 200 (OK) | 400 (Bad Request) | 503 (Service Unavailable) | 500 (Internal Error)
  - Input: Named raw customer feature object
   - Output: Prediction, probability, model version

3. **GET /docs**
   - Swagger UI interactive documentation

4. **GET /openapi.json**
   - OpenAPI schema (JSON)

**Lifespan Management**:
- On startup: Load Production model from MLflow
- On shutdown: Clean up resources
- Error handling: If model fails to load, return 503 for predictions

### 2.5 Pydantic Models

**File**: `src/api/models.py`

**Models**:
- `ChurnPredictionRequest`: Validates named raw fields or compatible feature lists
- `ChurnPredictionResponse`: Ensures output format (prediction, probability, version)
- `HealthCheckResponse`: Ensures health check response format

**Benefits**:
- Type safety and validation
- Auto-generated Swagger UI documentation
- Clear request/response contracts
- Error messages for invalid data

## 3. Data Flow Diagrams

### 3.1 Training Flow

```
┌─────────────────────┐
│   Raw Dataset       │
│  (CSV, 7K rows)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Data Preprocessing                     │
│  ├─ Handle missing values               │
│  ├─ Identify feature types              │
│  ├─ OneHotEncode categorical            │
│  ├─ StandardScale numeric               │
│  └─ Return (X, y, preprocessor)         │
└──────────┬──────────────────────────────┘
           │
           ├─────────────────┐
           │                 │
           ▼                 ▼
      ┌─────────┐       ┌──────────┐
      │  X_train│       │ X_test   │
      │  y_train│       │ y_test   │
      └────┬────┘       └─────┬────┘
           │                  │
           └────────┬─────────┘
                    ▼
         ┌──────────────────────┐
         │ Train LR Model       │
         │ fit(X_train, y_train)│
         └────────┬─────────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │ Evaluate on Test Set │
         │ ├─ accuracy          │
         │ ├─ precision         │
         │ ├─ recall            │
         │ └─ f1_score          │
         └────────┬─────────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │   Log to MLflow      │
         │ ├─ parameters        │
         │ ├─ metrics           │
         │ ├─ model artifact    │
         │ └─ git commit hash   │
         └────────┬─────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  Model Registry             │
    │  "ChurnPredictionModel"      │
    │  ├─ v1 (Staging)            │
    │  ├─ v2 (Production) ◄───────┼─ Transitioned
    │  └─ v3 (None)               │
    └─────────────────────────────┘
```

### 3.2 Inference Flow

```
┌─────────────────────┐
│  Client Request     │
│  POST /predict      │
│  {features: [...]}  │
└──────────┬──────────┘
           │
           ▼
┌────────────────────────────────┐
│  FastAPI Endpoint              │
│  predict_churn()               │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  Pydantic Validation           │
│  ChurnPredictionRequest         │
│  - Validate features list       │
│  - Type checking                │
└────────────────┬───────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
       ▼                   ▼
  [Valid]             [Invalid]
       │                   │
       │                   ▼
       │         ┌──────────────────┐
       │         │ HTTP 400         │
       │         │ Bad Request      │
       │         │ Error details    │
       │         └──────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Check Model Availability      │
│  if MODEL is None:             │
│    return HTTP 503             │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  Convert to DataFrame          │
│  pd.DataFrame([request.dict()])│
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  MODEL.predict(input_df)       │
│  MODEL.predict_proba(input_df) │
└────────────────┬───────────────┘
                 │
                 ├─ prediction: int (0 or 1)
                 └─ probability: float (0.0-1.0)
                 │
                 ▼
┌────────────────────────────────┐
│  ChurnPredictionResponse       │
│  {                             │
│    prediction: 1,              │
│    probability: 0.75,          │
│    model_version: "2"          │
│  }                             │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  HTTP 200 OK                   │
│  Return JSON Response          │
└────────────────────────────────┘
```

## 4. Container Architecture

### 4.1 Docker Compose Orchestration

```yaml
services:
  mlflow:
    build: Dockerfile.mlflow
    volumes:
      - mlflow_data:/app/mlruns        # Persist experiments
      - mlflow_artifacts:/app/mlartifacts  # Persist model artifacts
    ports:
      - "5000:5000"
    networks:
      - churn_network

  api:
    build: Dockerfile.api
    depends_on:
      - mlflow                          # Wait for MLflow startup
    ports:
      - "8000:8000"
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    networks:
      - churn_network
```

### 4.2 Service Communication

```
┌──────────────────────────────────────────────────┐
│          Docker Bridge Network                   │
│           (churn_network)                        │
│                                                  │
│  ┌─────────────────────┐    ┌────────────────┐  │
│  │   mlflow:5000       │    │    api:8000    │  │
│  │                     │◄──►│                │  │
│  │  (DNS resolution)   │    │  (HTTP calls)  │  │
│  └─────────────────────┘    └────────────────┘  │
│                                                  │
└──────────────────────────────────────────────────┘

DNS: "mlflow" resolves to mlflow container's IP
HTTP: http://mlflow:5000 → MLflow server (internal to network)
```

## 5. Error Handling Strategy

### 5.1 API Layer Error Handling

```python
try:
    # Validate input (Pydantic handles this)
    input_df = pd.DataFrame([request.dict()])
    
    # Check model availability
    if MODEL is None:
        raise HTTPException(status_code=503)
    
    # Make prediction
    prediction = MODEL.predict(input_df)[0]
    probability = MODEL.predict_proba(input_df)[0, 1]
    
    return ChurnPredictionResponse(...)
    
except ValidationError as e:
    # HTTP 400: Bad Request (invalid input data)
    raise HTTPException(status_code=400, detail=str(e))
    
except ValueError as e:
    # HTTP 400: Bad Request (invalid values)
    raise HTTPException(status_code=400, detail=str(e))
    
except Exception as e:
    # HTTP 500: Internal Server Error
    raise HTTPException(status_code=500, detail=str(e))
```

### 5.2 HTTP Status Codes

| Status | Meaning | Cause |
|--------|---------|-------|
| 200 | OK | Successful prediction |
| 400 | Bad Request | Invalid input data, validation failed |
| 422 | Unprocessable Entity | Pydantic validation error |
| 500 | Internal Server Error | Model error, unexpected exception |
| 503 | Service Unavailable | Model not loaded, MLflow unreachable |

## 6. Scalability Considerations

### 6.1 Horizontal Scaling

```
┌─────────────────────────────────────────────────┐
│           Load Balancer (Nginx/HAProxy)         │
│  ┌──────────────────────────────────────────┐   │
│  │  Round-robin / Least connections         │   │
│  └──────────────────────────────────────────┘   │
└────────────────────────────────────────────┬────┘
         ┌──────────────┬──────────────┐
         │              │              │
         ▼              ▼              ▼
    ┌────────┐     ┌────────┐    ┌────────┐
    │ API #1 │     │ API #2 │    │ API #3 │
    └────────┘     └────────┘    └────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
                   MLflow Server
                  (Single instance)
```

### 6.2 Performance Optimization

1. **Model Caching**: Load model once at startup, reuse across requests
2. **Batch Prediction**: Add `/batch_predict` endpoint for bulk requests
3. **Connection Pooling**: MLflow client uses HTTP connection pooling
4. **Feature Validation**: Pydantic pre-validates inputs before model inference
5. **Monitoring**: Add Prometheus metrics for latency, throughput, errors

## 7. Security Considerations

### 7.1 Current Implementation

- Non-root user in Docker containers (UID 1000)
- No hardcoded credentials in code
- Environment variables for sensitive configuration
- Validation of all inputs (Pydantic)
- Error messages don't leak sensitive information

### 7.2 Production Enhancements

- HTTPS/TLS for API endpoints
- Authentication & Authorization (API keys, OAuth2)
- CORS policy configuration
- Rate limiting on /predict endpoint
- Input size limits
- Logging and audit trails
- Secrets management (AWS Secrets Manager, HashiCorp Vault)

## 8. Monitoring & Observability

### 8.1 Health Checks

```yaml
# Docker health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 8.2 Logging

```python
# Structured logging
logger.info(f"Model loaded: {MODEL_VERSION}")
logger.error(f"Prediction failed: {e}")
logger.warning(f"Could not connect to MLflow")
```

### 8.3 Metrics (Recommended)

- **Request Latency**: Histogram of prediction latency
- **Error Rate**: Count of HTTP 4xx/5xx responses
- **Model Latency**: Time for model.predict()
- **Throughput**: Requests per second
- **Model Version**: Track which model version is in use

---

## Conclusion

This architecture prioritizes:
1. **Simplicity**: Easy to understand and maintain
2. **Modularity**: Separate concerns (data, model, API)
3. **Scalability**: Stateless API design, flexible infrastructure
4. **Robustness**: Comprehensive error handling and validation
5. **Observability**: Health checks and logging

For production deployments, consider adding Kubernetes orchestration, database logging, advanced monitoring, and enhanced security measures.
