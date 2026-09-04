# Quick Start Guide

## 🚀 5-Minute Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git (to clone the repo)
- Telco Customer Churn dataset (see below)

### Step 1: Get the Dataset (5 min)

```bash
# Option A: Manual Download (Recommended)
# 1. Download from: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
# 2. Extract: WA_Fn-UseC_-Telco-Customer-Churn.csv
# 3. Place in: data/ directory
#    churn-prediction-api-mlflow/
#    └── data/
#        └── WA_Fn-UseC_-Telco-Customer-Churn.csv

# Option B: Verify Dataset
python setup_dataset.py
```

### Step 2: Train Model (Optional - 1-2 min)

```bash
# Start MLflow container
docker-compose up mlflow -d
sleep 5

# Train model (logs to MLflow)
docker-compose run --rm api python -m src.model.train

# Stop MLflow
docker-compose down
```

### Step 3: Start Full Stack (< 1 min)

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Verify health
curl http://localhost:8000/health
# Expected: {"status":"ok","model_status":"loaded",...}
```

### Step 4: Make Predictions (30 sec)

```bash
# Predict churn
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [0.5, 0.2, 0.1, 0.9, 0.3, 0.4, 0.6, 0.2, 0.8, 0.1, 0.3, 0.7, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.1]}'

# Expected response:
# {"prediction":1,"probability":0.75,"model_version":"1"}
```

### Step 5: Explore UIs (< 1 min)

```bash
# FastAPI Docs
open http://localhost:8000/docs

# MLflow UI (experiments, models, metrics)
open http://localhost:5000
```

---

## 📋 Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check API & model status |
| POST | `/predict` | Get churn prediction |
| GET | `/docs` | Interactive API documentation |
| GET | `/openapi.json` | OpenAPI schema |

---

## 🛑 Stop Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (clears MLflow data)
docker-compose down -v
```

---

## 🧪 Run Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_model.py -v  # Data preprocessing tests
pytest tests/test_api.py -v    # API endpoint tests
```

---

## 📁 Project Structure

```
churn-prediction-api-mlflow/
├── src/
│   ├── api/               # FastAPI application
│   │   ├── main.py       # Server & endpoints
│   │   └── models.py     # Pydantic schemas
│   ├── data/             # Data processing
│   │   └── preprocess.py # Loading & preprocessing
│   └── model/            # ML components
│       ├── train.py      # Training with MLflow
│       └── predict.py    # Prediction utilities
├── tests/                # Unit & integration tests
│   ├── test_model.py
│   └── test_api.py
├── data/                 # Place dataset here
├── Docker files          # Containerization
│   ├── Dockerfile.api
│   ├── Dockerfile.mlflow
│   └── docker-compose.yml
├── README.md             # Full documentation
├── ARCHITECTURE.md       # Architecture diagrams
└── setup_dataset.py      # Dataset setup helper
```

---

## ❌ Troubleshooting

### Model not loading?
```bash
# Check MLflow is running
curl http://localhost:5000

# Check logs
docker-compose logs mlflow
docker-compose logs api

# Verify model was trained
# Open http://localhost:5000 → Check Experiments tab
```

### Port 5000 or 8000 already in use?
```bash
# Kill process on port 5000 (Mac/Linux)
lsof -i :5000 | tail -1 | awk '{print $2}' | xargs kill -9

# Or edit docker-compose.yml and change ports
```

### Dataset file not found?
```bash
# Run setup helper
python setup_dataset.py

# This will guide you through dataset download
```

---

## 📚 Full Documentation

- **README.md** - Complete setup, features, and API documentation
- **ARCHITECTURE.md** - System design, data flows, and scalability
- **setup_dataset.py** - Interactive dataset setup guide

---

## 🎯 Key Features

✅ **Real-time Predictions** - Fast REST API  
✅ **MLflow Integration** - Complete experiment tracking  
✅ **Model Versioning** - Production stage management  
✅ **Containerized** - Docker + Docker Compose  
✅ **Well-Tested** - 15 automated tests  
✅ **Documented** - Comprehensive README & architecture guide  
✅ **Production-Ready** - Error handling, health checks, logging  

---

## 🆘 Support

1. Check **Troubleshooting** section in README.md
2. Review **ARCHITECTURE.md** for design details
3. Check application logs: `docker-compose logs -f`
4. Run tests: `pytest tests/ -v`

---

**Ready to deploy?** Follow README.md for comprehensive setup instructions.
