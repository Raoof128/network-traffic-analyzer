# API Reference

**Version**: 1.1.0
**Base URL**: `http://localhost:8000`
**API Type**: REST (JSON)
**Documentation**: OpenAPI/Swagger at `/docs`

---

## Quick Start

Start the API server:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Access interactive docs:
```
http://localhost:8000/docs
```

---

## Endpoints

### Root Endpoint

#### `GET /`

Returns API information and welcome message.

**Response:**
```json
{
  "message": "Network Traffic Analyzer API v1.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### Health Check

#### `GET /health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.1.0",
  "timestamp": "2025-11-14T10:30:00Z"
}
```

---

### Analyze PCAP

#### `POST /api/v1/analyze`

Submit a PCAP file for anomaly detection analysis.

**Request Body:**
```json
{
  "pcap_file": "/path/to/traffic.pcap",
  "model_path": "/path/to/model.pkl",
  "preprocessor_path": "/path/to/preprocessor.pkl"
}
```

**Response:**
```json
{
  "analysis_id": "abc123",
  "status": "completed",
  "total_packets": 1000,
  "anomalies_detected": 25,
  "anomaly_percentage": 2.5,
  "timestamp": "2025-11-14T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"pcap_file": "traffic.pcap", "model_path": "model.pkl"}'
```

---

### Get Analysis Results

#### `GET /api/v1/analysis/{analysis_id}`

Retrieve results from a previous analysis.

**Parameters:**
- `analysis_id` (path): Unique analysis identifier

**Response:**
```json
{
  "analysis_id": "abc123",
  "status": "completed",
  "results": {
    "total_packets": 1000,
    "anomalies": 25,
    "details": [...]
  }
}
```

---

### List Models

#### `GET /api/v1/models`

Get list of available trained models.

**Response:**
```json
{
  "models": [
    {
      "name": "isolation_forest",
      "path": "/models/isolation_forest.pkl",
      "size": "1.2 MB",
      "created": "2025-11-01T00:00:00Z"
    }
  ]
}
```

---

### Get Model Info

#### `GET /api/v1/models/{model_name}`

Get detailed information about a specific model.

**Parameters:**
- `model_name` (path): Model filename

**Response:**
```json
{
  "name": "isolation_forest",
  "type": "unsupervised",
  "path": "/models/isolation_forest.pkl",
  "size": "1.2 MB",
  "metadata": {
    "algorithm": "Isolation Forest",
    "features": 30
  }
}
```

---

### Upload PCAP

#### `POST /api/v1/upload/pcap`

Upload a PCAP file for storage and later analysis.

**Request:**
- Content-Type: `multipart/form-data`
- File parameter: `file`

**Response:**
```json
{
  "filename": "traffic_20251114_103000.pcap",
  "path": "/uploads/traffic_20251114_103000.pcap",
  "size": "15.3 MB",
  "timestamp": "2025-11-14T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/upload/pcap \
  -F "file=@traffic.pcap"
```

---

### Get Statistics

#### `GET /api/v1/stats`

Get system and analysis statistics.

**Response:**
```json
{
  "total_analyses": 150,
  "total_packets_processed": 1500000,
  "total_anomalies_detected": 3750,
  "uptime_seconds": 86400,
  "memory_usage_mb": 1024
}
```

---

## Data Models

### AnalysisRequest

```python
{
  "pcap_file": str,              # Required: Path to PCAP file
  "model_path": str,             # Required: Path to trained model
  "preprocessor_path": str | None  # Optional: Path to preprocessor
}
```

### AnalysisResponse

```python
{
  "analysis_id": str,
  "status": str,                 # "pending" | "processing" | "completed" | "failed"
  "total_packets": int,
  "anomalies_detected": int,
  "anomaly_percentage": float,
  "timestamp": str,
  "error": str | None           # Error message if status == "failed"
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "pcap_file"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently no rate limiting implemented. Recommended for production:
- 100 requests/minute per IP
- 1000 requests/hour per IP

---

## Authentication

Currently no authentication required. For production, implement:
- API Keys
- JWT tokens
- OAuth 2.0

---

## Complete Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Upload PCAP
files = {"file": open("traffic.pcap", "rb")}
response = requests.post(f"{BASE_URL}/api/v1/upload/pcap", files=files)
uploaded_file = response.json()

# Analyze
analysis_request = {
    "pcap_file": uploaded_file["path"],
    "model_path": "/models/isolation_forest.pkl"
}
response = requests.post(f"{BASE_URL}/api/v1/analyze", json=analysis_request)
result = response.json()

print(f"Anomalies: {result['anomalies_detected']} out of {result['total_packets']}")
```

---

**For interactive documentation, visit**: `http://localhost:8000/docs`
