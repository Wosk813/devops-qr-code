from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import qrcode
from google.cloud import storage
from io import BytesIO
import google.auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage client
storage_client = storage.Client()
bucket_name = 'qr-code-devops-project'
bucket = storage_client.bucket(bucket_name)

@app.post("/generate-qr/")
async def generate_qr(url: str):
    try:
        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR Code to BytesIO object
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Generate file name for GCS
        # Sanitize filename to avoid storage errors
        safe_filename = url.split('//')[-1].replace('/', '_')
        file_name = f"qr_codes/{safe_filename}.png"

        try:
            # Upload to Google Cloud Storage
            print(f"Attempting to upload to GCS: {file_name}")  # Debug log
            blob = bucket.blob(file_name)
            blob.upload_from_file(
                img_byte_arr,
                content_type='image/png'
            )
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Generate the public URL
            public_url = blob.public_url
            return {"qr_code_url": public_url}
        except Exception as e:
            print(f"GCS upload error: {str(e)}")  # Debug log
            raise HTTPException(
                status_code=500, 
                detail=f"Error uploading to Google Cloud Storage: {str(e)}"
            )
    except Exception as e:
        print(f"QR generation error: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating QR code: {str(e)}"
        )

@app.get("/debug")
async def debug_credentials():
    # Sprawdź, jakie credentials są aktualnie używane
    credentials, project = google.auth.default()
    
    # Spróbuj pobrać informacje o service account
    storage_client = storage.Client()
    try:
        buckets = list(storage_client.list_buckets())
        return {
            "project": project,
            "credentials_type": str(type(credentials)),
            "service_account": credentials.service_account_email if hasattr(credentials, 'service_account_email') else None,
            "buckets": [b.name for b in buckets]
        }
    except Exception as e:
        return {"error": str(e)}
    