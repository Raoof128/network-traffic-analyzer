"""
FastAPI REST API for Network Traffic Analyzer
Provides endpoints for traffic analysis, model management, and monitoring
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Import analyzer components
try:
    from capture.pcap_handler import PcapHandler
    from features.extractor import FeatureExtractor, FlowAggregator
    from features.preprocessor import FeaturePreprocessor
    from models.unsupervised import IsolationForestDetector
    from detection.alert_manager import AlertManager, AlertSeverity
    from utils.validators import InputValidator, ValidationError
    from utils.secure_pickle import safe_load
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Network Traffic Analyzer API",
    description="ML-powered network traffic analysis and anomaly detection API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class AnalysisRequest(BaseModel):
    pcap_file: str = Field(..., description="Path to PCAP file")
    model_path: Optional[str] = Field(None, description="Path to trained model")
    preprocessor_path: Optional[str] = Field(None, description="Path to preprocessor")

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    total_packets: int
    total_flows: int
    anomaly_count: int
    anomaly_rate: float
    timestamp: str

class ModelInfo(BaseModel):
    name: str
    path: str
    type: str
    size_bytes: int
    modified: str

class AlertResponse(BaseModel):
    alert_id: int
    timestamp: str
    severity: str
    anomaly_type: str
    src_ip: Optional[str]
    dst_ip: Optional[str]
    src_port: Optional[int]
    dst_port: Optional[int]
    protocol: Optional[str]

# In-memory storage for analysis jobs (use database in production)
analysis_jobs: Dict[str, Dict[str, Any]] = {}

# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Network Traffic Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/api/v1/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_pcap(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze a PCAP file for anomalies

    Args:
        request: Analysis request with PCAP file path and optional model

    Returns:
        Analysis results with anomaly detection
    """
    try:
        # Validate PCAP file
        InputValidator.validate_pcap_file(request.pcap_file)

        # Generate analysis ID
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Load PCAP
        logger.info(f"Loading PCAP file: {request.pcap_file}")
        packets = PcapHandler.read_pcap(request.pcap_file)

        if not packets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PCAP file contains no packets"
            )

        # Extract features
        feature_extractor = FeatureExtractor()
        packet_df = feature_extractor.extract_batch_features(packets)

        # Aggregate to flows
        flow_aggregator = FlowAggregator()
        flow_df = flow_aggregator.create_flow_features(packets)

        # Perform anomaly detection if model provided
        anomaly_count = 0
        if request.model_path:
            try:
                # Load model securely
                model = safe_load(request.model_path, restricted=True)

                # Load preprocessor if provided
                preprocessor = None
                if request.preprocessor_path:
                    preprocessor = FeaturePreprocessor.load(request.preprocessor_path)

                # Prepare features
                if preprocessor:
                    X = preprocessor.transform(flow_df)
                else:
                    numeric_cols = flow_df.select_dtypes(include=['number']).columns.tolist()
                    exclude_cols = ['timestamp', 'start_time', 'end_time']
                    feature_cols = [c for c in numeric_cols if c not in exclude_cols]
                    X = flow_df[feature_cols].fillna(0)

                # Predict
                predictions = model.predict(X)
                anomaly_count = sum(predictions == -1) + sum(predictions == 1)

            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")
                # Continue without anomaly detection

        # Calculate statistics
        total_packets = len(packets)
        total_flows = len(flow_df)
        anomaly_rate = anomaly_count / total_flows if total_flows > 0 else 0.0

        # Store analysis results
        analysis_jobs[analysis_id] = {
            'status': 'completed',
            'total_packets': total_packets,
            'total_flows': total_flows,
            'anomaly_count': anomaly_count,
            'anomaly_rate': anomaly_rate,
            'timestamp': datetime.now().isoformat()
        }

        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            total_packets=total_packets,
            total_flows=total_flows,
            anomaly_count=anomaly_count,
            anomaly_rate=anomaly_rate,
            timestamp=datetime.now().isoformat()
        )

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/api/v1/analysis/{analysis_id}", tags=["Analysis"])
async def get_analysis(analysis_id: str):
    """
    Get analysis results by ID

    Args:
        analysis_id: Analysis ID

    Returns:
        Analysis results
    """
    if analysis_id not in analysis_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found"
        )

    return analysis_jobs[analysis_id]

@app.get("/api/v1/models", response_model=List[ModelInfo], tags=["Models"])
async def list_models():
    """
    List available trained models

    Returns:
        List of available models
    """
    models_dir = Path("models/trained_models")
    if not models_dir.exists():
        return []

    models = []
    for model_file in models_dir.glob("*.pkl"):
        stat = model_file.stat()
        models.append(ModelInfo(
            name=model_file.stem,
            path=str(model_file),
            type="pickle",
            size_bytes=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
        ))

    return models

@app.get("/api/v1/models/{model_name}", tags=["Models"])
async def get_model_info(model_name: str):
    """
    Get information about a specific model

    Args:
        model_name: Model name

    Returns:
        Model information
    """
    model_path = Path(f"models/trained_models/{model_name}.pkl")

    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_name} not found"
        )

    stat = model_path.stat()
    return ModelInfo(
        name=model_name,
        path=str(model_path),
        type="pickle",
        size_bytes=stat.st_size,
        modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
    )

@app.post("/api/v1/upload/pcap", tags=["Upload"])
async def upload_pcap(file: UploadFile = File(...)):
    """
    Upload a PCAP file for analysis

    Args:
        file: PCAP file upload

    Returns:
        Upload confirmation with file path
    """
    # Validate file extension
    if not file.filename.endswith(('.pcap', '.pcapng', '.cap')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Expected .pcap, .pcapng, or .cap"
        )

    # Save uploaded file
    upload_dir = Path("data/pcaps/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / filename

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return {
            "status": "success",
            "filename": filename,
            "path": str(file_path),
            "size_bytes": len(content)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

@app.get("/api/v1/stats", tags=["Statistics"])
async def get_statistics():
    """
    Get overall statistics

    Returns:
        System statistics
    """
    models_dir = Path("models/trained_models")
    pcaps_dir = Path("data/pcaps")

    return {
        "total_analyses": len(analysis_jobs),
        "total_models": len(list(models_dir.glob("*.pkl"))) if models_dir.exists() else 0,
        "total_pcaps": len(list(pcaps_dir.glob("*.pcap*"))) if pcaps_dir.exists() else 0,
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
