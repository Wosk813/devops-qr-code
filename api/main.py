from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import qrcode
from google.cloud import storage
import os
from io import BytesIO

# Loading Environment variable (Google Cloud credentials)
from dotenv import load_dotenv
import json
load_dotenv()

# Create temporary credentials file from .env
credentials_content = os.getenv("GOOGLE_CLOUD_CREDENTIALS")
if credentials_content:
    # Use absolute path in container
    temp_credentials_path = "/app/temp_credentials.json"
    try:
        # Parse the JSON string to ensure it's valid
        json_credentials = json.loads(credentials_content)
        
        # Write the credentials to a temporary file
        with open(temp_credentials_path, "w") as f:
            json.dump(json_credentials, f)
            
        # Set the environment variable to point to our temporary file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_credentials_path
        print(f"Credentials file created at: {temp_credentials_path}")
    except json.JSONDecodeError as e:
        print(f"Error parsing credentials JSON: {e}")
    except Exception as e:
        print(f"Error setting up credentials: {e}")
else:
    print("Warning: GOOGLE_CLOUD_CREDENTIALS environment variable not found")

# Initialize storage client after credentials are set up
try:
    storage_client = storage.Client()
    bucket_name = 'qr-code-devops-project'
    bucket = storage_client.bucket(bucket_name)
except Exception as e:
    print(f"Error initializing storage client: {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    