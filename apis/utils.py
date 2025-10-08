"""
Certificate processing utilities for the SEU Tools APIs.
Contains functions for extracting subscription months from GOSI certificates.
"""

import json
import time
import base64
import math

import requests
import magic
import pdf2image
import pdfplumber
import io
import re
import os
import logging
from typing import Dict, Optional
from PIL import Image
from openai import AzureOpenAI
from django.http import HttpResponse
from django.conf import settings
from decouple import config

# Set up processing logger
logger = logging.getLogger('processing')

def get_requester_name(request):
    """Get the requester name from the request auth or user."""
    if hasattr(request, 'auth') and request.auth:
        # For API Token authentication, request.auth is the APIToken instance
        if hasattr(request.auth, 'name'):
            return request.auth.name
        # For JWT authentication, request.auth is the token string
        elif isinstance(request.auth, str):
            return 'JWT Token'
    
    # If no token but user is authenticated (web interface)
    if hasattr(request, 'user') and request.user and request.user.is_authenticated:
        return f"Web: {request.user.username}"
    
    return 'Web Interface'

def extract_subscription_months_from_pdf(file_content: bytes, filename: str) -> Dict[str, str]:
    """
    Extract total subscription months from a certificate PDF using text extraction.
    
    This function processes both Arabic and English GOSI certificates to extract
    the total subscription months value. It uses direct PDF text extraction
    and supports both formats:
    - Arabic: Looks for "ﺮﻬﺷ" pattern
    - English: Looks for numbers followed by "Months"
    
    Parameters:
    ----------
    file_content : bytes
        The PDF file content
    filename : str
        The name of the uploaded file
    
    Returns:
    -------
    Dict[str, str]
        A dictionary containing:
        - status: "success" or "error"
        - subscription_months: The extracted number of months (if successful) or NA
        - subscription_years: The equivalent in years (if successful) or NA
        - mock: Whether the result is a mock or not (if successful)
            - error_message: Error details (if failed)
            - debug_text: Debug information (if failed)
    
    """
    try:
        # Open PDF with pdfplumber
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
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
                    "subscription_years": math.floor(int(subscription_months) / 12),
                    "SSN": extract_SSN_from_pdf(file_content, filename),
                    #"QR_URL": extract_url_from_qr(file_content, filename),
                    "mock": False
                }
            else:
                return {
                    "status": "success",
                    "error_message": "Could not find subscription months information in the document",
                    "subscription_months": "NA",
                    "subscription_years": "NA",
                    "SSN": "NA",
                    "mock": False,
                }
    
    except Exception as e:
        logger.error(f"Error processing certificate {filename}: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error processing PDF: {str(e)}"
        }

def extract_SSN_from_pdf(file_content: bytes, filename: str) -> Dict[str, str]:
    """
    Extract SSN from a certificate PDF using text extraction.
    
    This function processes both Arabic and English GOSI certificates to extract
    the SSN value. It uses direct PDF text extraction
    and supports both formats:
    - Arabic: Looks for "رقم الهوية الوطنية/الإقامة" pattern
    - English: Looks for "National ID/IQAMAH" pattern
    
    Parameters:
    ----------
    file_content : bytes
        The PDF file content
    filename : str
        The name of the uploaded file
    
    Returns:
    -------
    str
        The extracted SSN value
    """
    try:
        # Open PDF with pdfplumber
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            # Get the first page
            page = pdf.pages[0]

            lookup_text = ["ﺔﻣﺎﻗﻹﺍ / ﺔﻴﻨﻃﻮﻟﺍ ﺔﻳﻮﻬﻟﺍ ﻢﻗﺭ", "National ID/IQAMAH"]
            
            # Extract text with layout preservation
            text = page.extract_text()
            lines = text.split('\n')
            
            debug_text = []
            SSN = None
            SSN = lines[7].split(" ")[0]
            #English version
            if SSN.isdigit() and len(SSN) == 10:
               
                return SSN
            else:
               SSN= lines[6].split(" ")[2]
               if SSN.isdigit() and len(SSN) == 10:
                 
                   return SSN
               else:
                   return "SSN not found"
            
            
    
    except Exception as e:
        logger.error(f"Error processing certificate {filename}: {str(e)}")
        return "SSN not found"

def process_pdf_with_ai(client: AzureOpenAI, file_content: bytes, filename: str, content_type: str) -> str:
    """Process PDF file by converting first page to image and using vision model."""
    try:
        # Convert first page of PDF to image
        images = pdf2image.convert_from_bytes(file_content, first_page=1, last_page=1)
        
        if not images:
            raise ValueError("Could not convert PDF to image")
        
        # Get the first (and only) page
        first_page = images[0]
        
        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        
        ai_response = process_image_with_ai(client, image_bytes, "image/png")
        
        return ai_response
        
        
    except Exception as e:
        logger.error(f"Error converting PDF to image: {str(e)}")
        raise ValueError(f"Could not process PDF: {str(e)}")

def process_image_with_ai(client: AzureOpenAI, file_content: bytes, file_type: str) -> str:
    """Process image file using Azure OpenAI Chat Completions API with vision."""
    base64_image = base64.b64encode(file_content).decode('utf-8')
    
    response = client.chat.completions.create(
        model=config("AZURE_OPEN_AI_MODEL_NAME"),
        messages=[
            {
                "role": "system",
                "content": """You are an AI assistant specialized in analyzing GOSI certificates. 
                    Your task is to extract the total subscription months (إجمالي أشهر الإشتراك or Total Subscription Months) 
                    and calculate the equivalent in years. also extract the (National ID / IQAMAH or رقم الهوية / الإقامة) from the certificate.
                    Respond only in valid JSON format with two fields:
                    - subscription_months: the exact number of months
                    - subscription_years: the equivalent in years (rounded)
                    - SSN: the National ID / IQAMAH (if found)
                    - QR_URL: the URL from the QR code in the certificate.
                    - mock: whether the result is a mock or not (if successful)
                    """
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this GOSI certificate image and extract the total subscription months,years, the National ID / IQAMAH. Return only a JSON response."
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
        max_tokens=800,
        temperature=1.0,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    print("response", response.choices[0].message.content)
    return response.choices[0].message.content

def parse_ai_response(ai_response: str) -> Dict[str, str]:
    """Parse AI response and extract subscription months and years."""
    logger.debug(f"AI Response: {ai_response}")
    
    try:
        # Extract JSON from the response (it might be wrapped in ```json blocks)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = ai_response
        
        response_json = json.loads(json_str)
        # Recalculate subscription_years using math.floor for consistency
        subscription_months = int(response_json['subscription_months'])
        subscription_years = math.floor(subscription_months / 12)
        
        if int(response_json['subscription_months']) > 0:
            return {
                "status": "success",
                "subscription_months": str(response_json['subscription_months']) ,
                "subscription_years": str(subscription_years) ,
                "SSN": response_json.get('SSN', 'NA'),
                "mock": response_json.get('mock', False)
            }
        else:
            return {
                "status": "success",
                "error_message": "Could not find subscription months information in the document",
                "subscription_months": "NA",
                "subscription_years": "NA",
                "SSN": "NA",
                "mock": False,
            }
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing AI response: {str(e)}")
        raise ValueError(f"Could not parse AI response: {ai_response}")

def extract_subscription_months_with_ai(file_content: bytes, filename: str, content_type: str) -> Dict[str, str]:
    """
    Extract total subscription months from a certificate using AI analysis.
    
    This function processes both PDF and image files using Azure OpenAI's vision model
    to extract subscription months information from GOSI certificates.
    
    Parameters:
    ----------
    file_content : bytes
        The file content (PDF or image)
    filename : str
        The name of the uploaded file
    content_type : str
        The MIME type of the file
    
    Returns:
    -------
    Dict[str, str]
        A dictionary containing:
        - status: "success" or "error"
        - subscription_months: The extracted number of months (if successful)
        - subscription_years: The equivalent in years (if successful)
        - mock: Whether the result is a mock or not (if successful)
            - error_message: Error details (if failed)
            - debug_text: Debug information (if failed)
        - error_message: Error details (if failed)
    """
    try:
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            azure_endpoint=config("AZURE_OPEN_AI_ENDPOINT"),
            api_key=config("AZURE_OPEN_AI_KEY"),
            api_version=config("AZURE_OPEN_AI_API_VERSION")
        )
        
        # Detect file type
        file_type = magic.from_buffer(file_content, mime=True)
        logger.info(f"Detected file type: {file_type}")
        
        # Process based on file type
        if file_type == "application/pdf":
            ai_response = process_pdf_with_ai(client, file_content, filename, content_type)
        elif file_type.startswith("image/"):
            ai_response = process_image_with_ai(client, file_content, file_type)
        else:
            return {
                "status": "error",
                "error_message": f"Unsupported file type: {file_type}. Please upload a PDF or image file."
            }
        
        # Parse and return the response
        result = parse_ai_response(ai_response)
        return result
        
    except Exception as e:
        logger.error(f"Error processing certificate {filename} with AI: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e)
        }

