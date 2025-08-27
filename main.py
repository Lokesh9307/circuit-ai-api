import os, uuid
from pathlib import Path
from typing import Optional
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from google.cloud import storage   # ✅ GCS client

from netlist.llm import call_gemini_for_netlist, call_gemini_for_explanation, call_gemini_for_arduino
from netlist.rules import rule_based_netlist
from draw.render import draw_from_netlist

# Optional .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = FastAPI(title="Text-to-Circuit API", version="1.0.0")

# CORS (allow local frontend dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenRequest(BaseModel):
    query: str
    force_fallback: Optional[bool] = None


@app.get("/", response_class=HTMLResponse)
async def home():
    return "<h3>Text-to-Circuit API</h3><p>POST /generate with JSON { query, force_fallback? }</p>"

@app.get("/health")
async def health():
    return {"ok": True, "gemini": bool(os.getenv("GEMINI_API_KEY"))}

def upload_to_gcs(local_file: Path, bucket_name: str) -> str:
    """Uploads file to GCS and returns signed URL"""
    
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
    
    # storage_client = storage.Client.from_service_account_json(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # unique filename
    blob_name = f"circuit_images/{uuid.uuid4().hex}.png"
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(local_file))

    # Generate signed URL (valid for 1 hour)
    url = blob.generate_signed_url(
        version="v4",
        expiration=3600,  # seconds → 1 hour
        method="GET"
    )
    return url



@app.post("/generate")
async def generate(req: GenRequest):
    # Step 1: Generate netlist
    netlist = None
    if not req.force_fallback:
        netlist = call_gemini_for_netlist(req.query)
    if not netlist:
        netlist = rule_based_netlist(req.query)

    # Step 2: Generate explanation & Arduino code
    explanation = call_gemini_for_explanation(req.query, netlist) or "Explanation unavailable."
    arduino_code = call_gemini_for_arduino(req.query, netlist) or "// Arduino code unavailable."

    # Step 3: Draw image locally
    out_dir = Path(__file__).resolve().parent / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"circuit_{uuid.uuid4().hex}.png"

    try:
        draw_from_netlist(netlist, out_file)
    except Exception as e:
        print("⚠️ Draw failed:", e)
        return JSONResponse({"error": "Failed to render image"}, status_code=500)

    # Step 4: Upload to GCS and get signed URL
    bucket_name = os.getenv("GCS_BUCKET", "circuit-image-storage")  # set in .env
    try:
        image_url = upload_to_gcs(out_file, bucket_name)
    except Exception as e:
        print("⚠️ GCS upload failed:", e)
        image_url = ""
        
    print(f"Image uploaded to: {image_url}")

    # Step 5: Return only what frontend needs
    return JSONResponse({
        "image_url": image_url,
        "explanation": explanation,
        "arduino_code": arduino_code
    })