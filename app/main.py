from fastapi import FastAPI, UploadFile, HTTPException, Depends, status, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBasic, HTTPBasicCredentials
from openai import AzureOpenAI
import pdfplumber
import io
import logging
import re
from typing import Dict, Union, List
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import ipaddress
from pathlib import Path
import json
import time
import time
import base64
import magic
import pdf2image
from PIL import Image

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and critical messages
    format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("app.log")  # File output
    ]
)
logger = logging.getLogger(__name__)

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-here-please-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
ALLOW_LOGIN_BY_USERNAME_PASSWORD = os.getenv("ALLOW_LOGIN_BY_USERNAME_PASSWORD", "false").lower() == "true"
logger.info(f"Username/Password authentication enabled: {ALLOW_LOGIN_BY_USERNAME_PASSWORD}")



# IP Restrictions
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "127.0.0.1").split(",")

# CORS Settings
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme with auto_error=False to allow falling back to basic auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
security_basic = HTTPBasic(auto_error=False)

# Mock user database - In production, use a real database
USERS_DB = {
    os.getenv("ADMIN_USERNAME", "admin"): {
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "hashed_password": pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin123")),
    }
}

def is_ip_allowed(ip: str) -> bool:
    """Check if an IP address is in the allowed list."""
    try:
        addr = ipaddress.ip_address(ip)
        for allowed in ALLOWED_IPS:
            try:
                if "/" in allowed:
                    network = ipaddress.ip_network(allowed.strip())
                    if addr in network:
                        return True
                else:
                    if addr == ipaddress.ip_address(allowed.strip()):
                        return True
            except ValueError:
                logger.warning(f"Invalid IP or CIDR in ALLOWED_IPS: {allowed}")
        return False
    except ValueError:
        logger.error(f"Invalid IP address: {ip}")
        return False

app = FastAPI(
    title="SEU GOSI Certificate Parser",
    description="""
    API for extracting subscription months from GOSI certificates.
    Supports both Arabic (إجمالي أشهر الإشتراك) and English (Total Months) formats.
    Uses direct PDF text extraction for accurate results.
    
    Authentication required for all endpoints except /docs and /redoc.
    IP address restrictions apply.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def ip_restriction_middleware(request: Request, call_next):
    """Middleware to check if the client IP is allowed."""
    client_ip = request.client.host
    
    # Allow access to documentation without IP restriction
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    if not is_ip_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for IP {client_ip}"
        )
    
    return await call_next(request)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Union[Dict, None]:
    """Get user from database."""
    if username in USERS_DB:
        return USERS_DB[username]
    return None

def authenticate_user(username: str, password: str) -> Union[Dict, bool]:
    """Authenticate a user."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: Dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_flexible(
    token: str = Depends(oauth2_scheme),
    credentials: HTTPBasicCredentials = Depends(security_basic)
) -> Dict:
    """Get current user from either token or username/password."""
    logger.debug(f"Attempting authentication - Token present: {bool(token)}, Credentials present: {bool(credentials)}")
    
    # Try token authentication first
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is not None:
                user = get_user(username)
                if user is not None:
                   
                    return user
        except JWTError as e:
            logger.warning(f"Token authentication failed: {str(e)}")
    
    # Try username/password if enabled
    if ALLOW_LOGIN_BY_USERNAME_PASSWORD and credentials:
        try:
            
            user = authenticate_user(credentials.username, credentials.password)
            if user:
                
                return user
            else:
                logger.warning(f"Basic auth failed for user: {credentials.username}")
        except Exception as e:
            logger.error(f"Error during basic auth: {str(e)}")
    
    # If we reach here, neither authentication method worked
    auth_methods = []
    if token:
        auth_methods.append("invalid token")
    if ALLOW_LOGIN_BY_USERNAME_PASSWORD and credentials:
        auth_methods.append("invalid username/password")
    elif ALLOW_LOGIN_BY_USERNAME_PASSWORD:
        auth_methods.append("no credentials provided")
    
    detail = "Not authenticated"
    if auth_methods:
        detail = f"Authentication failed: {', '.join(auth_methods)}"
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": 'Basic realm="Login Required"' if ALLOW_LOGIN_BY_USERNAME_PASSWORD else "Bearer"},
    )

@app.post("/token")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """
    Get access token using username and password.
    
    Returns:
    -------
    Dict[str, str]
        Access token and token type
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/extract-subscription-months/", 
    response_model=Dict[str, str],
    responses={
        200: {
            "description": "Successfully extracted subscription months",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "subscription_months": "177",
                        "field_name": "Total Subscription Months / إجمالي أشهر الإشتراك"
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed"
        },
        403: {
            "description": "IP address not allowed"
        },
        404: {
            "description": "Subscription months not found in document",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "message": "Could not find subscription months information in the document",
                            "debug_text": ["Line contents..."]
                        }
                    }
                }
            }
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error message"
                    }
                }
            }
        }
    }
)
async def extract_subscription_months(
    request: Request,
    file: UploadFile,
    current_user: Dict = Depends(get_current_user_flexible)
) -> Dict[str, str]:
    """
    Extract total subscription months from a certificate PDF.
    
    This endpoint processes both Arabic and English SEU certificates to extract
    the total subscription months value. It uses direct PDF text extraction
    and supports both formats:
    - Arabic: Looks for "ﺮﻬﺷ" pattern
    - English: Looks for numbers followed by "Months"
    
   
    
    Parameters:
    ----------
    request : Request
        The FastAPI request object
    file : UploadFile
        The PDF certificate file to process. Must be a valid PDF document.
    current_user : Dict
        The authenticated user (injected by FastAPI)
    
    Returns:
    -------
    Dict[str, str]
        A dictionary containing:
        - status: "success"
        - subscription_months: The extracted number of months
        - field_name: Bilingual field name
    
    Raises:
    ------
    HTTPException
        - 401: If authentication fails
        - 403: If IP address is not allowed
        - 404: If subscription months information cannot be found
        - 500: If there's an error processing the file
    """
    try:
        content = await file.read()
        
        # Open PDF with pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            # Get the first page
            page = pdf.pages[0]
            
            # Extract text with layout preservation
            text = page.extract_text()
            lines = text.split('\n')
            
            debug_text = []
            subscription_months = None
            
            # Search for the target text and extract the number
            for i, line in enumerate(lines):
                debug_text.append(f"Line {i}: {line}")
                
                # Try Arabic format first
                if "ﺮﻬﺷ" in line:
                    # Split by "ﺮﻬﺷ" to get all numbers
                    parts = line.split("ﺮﻬﺷ")
                    numbers = []
                    for part in parts:
                        nums = re.findall(r'\d+', part)
                        if nums:
                            numbers.extend(nums)
                    
                    # Find the largest number (which should be the total)
                    if numbers:
                        largest_num = max(int(num) for num in numbers)
                        subscription_months = str(largest_num)
                        break
                
                # Try English format
                elif "Months" in line:
                    # Extract all numbers followed by "Months"
                    numbers = re.findall(r'(\d+)\s*Months', line)
                    if numbers:
                        # Find the largest number (which should be the total)
                        largest_num = max(int(num) for num in numbers)
                        subscription_months = str(largest_num)
                        break
            
            if subscription_months:
                return {
                    "status": "success",
                    "subscription_months": subscription_months,
                    "subscription_years": str(int(int(subscription_months) / 12)),
                    
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": "Could not find subscription months information in the document. Please check the document and try again.",
                        "debug_text": debug_text
                    }
                )

    except Exception as e:
        logger.error(f"Error processing certificate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_pdf_with_ai(client: AzureOpenAI, file_content: bytes, filename: str, content_type: str) -> str:
    """Process PDF file by converting first page to image and using vision model."""
    try:
        # Convert first page of PDF to image
        images = pdf2image.convert_from_bytes(file_content, first_page=1, last_page=1)
        
        if not images:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not convert PDF to image"
            )
        
        # Get the first (and only) page
        first_page = images[0]
        
        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        
        # Convert to base64 for the API
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Use vision model to analyze the image
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPEN_AI_MODEL_NAME"),  # Make sure this supports vision
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant specialized in analyzing GOSI certificates. 
                    Your task is to extract the total subscription months (إجمالي أشهر الإشتراك or Total Subscription Months) 
                    and calculate the equivalent in years. 
                    Respond only in valid JSON format with two fields:
                    - subscription_months: the exact number of months
                    - subscription_years: the equivalent in years (rounded)"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this GOSI certificate (converted from PDF first page) and extract the total subscription months. Return only a JSON response."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error converting PDF to image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not process PDF: {str(e)}"
        )

async def process_image_with_ai(client: AzureOpenAI, file_content: bytes, file_type: str) -> str:
    """Process image file using Azure OpenAI Chat Completions API with vision."""
    base64_image = base64.b64encode(file_content).decode('utf-8')
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPEN_AI_MODEL_NAME"),  # Make sure this supports vision
        messages=[
            {
                "role": "system",
                "content": """You are an AI assistant specialized in analyzing GOSI certificates. 
                Your task is to extract the total subscription months (إجمالي أشهر الإشتراك or Total Subscription Months) 
                and calculate the equivalent in years. 
                Respond only in valid JSON format with two fields:
                - subscription_months: the exact number of months
                - subscription_years: the equivalent in years (rounded)"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this GOSI certificate image and extract the total subscription months. Return only a JSON response."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{file_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    
    return response.choices[0].message.content

def parse_ai_response(ai_response: str) -> Dict[str, str]:
    """Parse AI response and extract subscription months and years."""
    logger.debug(f"AI Response: {ai_response}")
    print(ai_response.replace("```json", "").replace("```", ""))
    
    try:
        # Extract JSON from the response (it might be wrapped in ```json blocks)
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = ai_response
        
        response_json = json.loads(json_str)
        
        return {
            "status": "success",
            "subscription_months": str(response_json['subscription_months']),
            "subscription_years": str(response_json['subscription_years'])
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing AI response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not parse AI response: {ai_response}"
        )

@app.post("/extract-subscription-months-by-AI/", 
    response_model=Dict[str, str],
    responses={
        200: {
            "description": "Successfully extracted subscription months",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "subscription_months": "177",
                        "subscription_years": "14",
                        "processing_time_seconds": "12.45",
                        "total_time_seconds": "13.02"
                    }
                }
            }
        },
        400: {
            "description": "Invalid file format or processing error"
        },
        401: {
            "description": "Authentication failed"
        },
        403: {
            "description": "IP address not allowed"
        },
        500: {
            "description": "Server error"
        }
    }
)
async def extract_subscription_months_by_AI(
    request: Request,
    file: UploadFile,
    current_user: Dict = Depends(get_current_user_flexible)
) -> Dict[str, str]:
    # Start timing
    start_time = time.time()
    
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPEN_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPEN_AI_KEY"),
            api_version=os.getenv("AZURE_OPEN_AI_API_VERSION")
        )

        file_content = await file.read()
        
        # Detect file type
        file_type = magic.from_buffer(file_content, mime=True)
        logger.info(f"Detected file type: {file_type}")
        
        # Track processing start time
        processing_start_time = time.time()
        
        # Process based on file type
        if file_type == "application/pdf":
            ai_response = await process_pdf_with_ai(
                client, file_content, file.filename, file.content_type
            )
        elif file_type.startswith("image/"):
            ai_response = await process_image_with_ai(
                client, file_content, file_type
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_type}. Please upload a PDF or image file."
            )

        # Track processing end time
        processing_end_time = time.time()
        processing_time = processing_end_time - processing_start_time
        
        # Parse and return the response
        result = parse_ai_response(ai_response)
        
        # Calculate total time
        end_time = time.time()
        total_time = end_time - start_time
        
        # Add timing information to the response
        result["processing_time_seconds"] = f"{processing_time:.2f}"
        result["total_time_seconds"] = f"{total_time:.2f}"
        
        logger.info(f"Request completed - Processing time: {processing_time:.2f}s, Total time: {total_time:.2f}s")
        
        return result

    except Exception as e:
        # Calculate time even for errors
        end_time = time.time()
        total_time = end_time - start_time
        logger.error(f"Error processing certificate (after {total_time:.2f}s): {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")  
async def root(
    request: Request,
    current_user: Dict = Depends(get_current_user_flexible)
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Root endpoint that shows API information.
    
    Parameters:
    ----------
    request : Request
        The FastAPI request object
    current_user : Dict
        The authenticated user (injected by FastAPI)
    
    Returns:
    -------
    Dict
        A dictionary containing:
        - name: API name
        - version: API version
        - description: API description
        - endpoints: Available endpoints and their descriptions
    
    Raises:
    ------
    HTTPException
        - 401: If authentication fails
        - 403: If IP address not allowed
    """
    return {
        "name": "SEU Tool API",
        "version": "1.0.0",
        "description": "API for extracting subscription months from SEU certificates (Arabic and English) and other tools",
        "endpoints": {
            "/token": "POST - Get access token",
            "/extract-subscription-months/": "POST - Extract total subscription months from a certificate PDF (Arabic/English)",
            "/extract-subscription-months-by-AI/": "POST - Extract total subscription months from a certificate PDF (Arabic/English) by AI model"
        }
    } 