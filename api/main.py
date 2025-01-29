from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import boto3
import os
from io import BytesIO

# Loading Environment variable (AWS Access Key and Secret Key)
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Allowing CORS for local testing
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
s3 = boto3.client(
    's3',
    aws_access_key_id= os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key= os.getenv("AWS_SECRET_KEY"))

bucket_name = 'qrcodeproject01' # Add your bucket name here

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

        # Generate file name for S3
        # Sanitize filename to avoid S3 errors
        safe_filename = url.split('//')[-1].replace('/', '_')
        file_name = f"qr_codes/{safe_filename}.png"

        try:
            # Upload to S3
            print(f"Attempting to upload to S3: {file_name}")  # Debug log
            s3.put_object(
                Bucket=bucket_name, 
                Key=file_name, 
                Body=img_byte_arr, 
                ContentType='image/png', 
                ACL='public-read'
            )
            
            # Generate the S3 URL
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
            return {"qr_code_url": s3_url}
        except Exception as e:
            print(f"S3 upload error: {str(e)}")  # Debug log
            raise HTTPException(
                status_code=500, 
                detail=f"Error uploading to S3: {str(e)}"
            )
    except Exception as e:
        print(f"QR generation error: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating QR code: {str(e)}"
        )
    