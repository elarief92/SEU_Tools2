# SEU GOSI Certificate Parser API

A FastAPI-based service for extracting subscription months from GOSI (General Organization for Social Insurance) certificates. The API supports both Arabic and English certificate formats and uses direct PDF text extraction for accurate results.

## Features

- Extract subscription months from GOSI certificates
- Support for both Arabic and English certificate formats
- Direct PDF text extraction (no OCR required)
- Secure authentication system
- IP address restrictions
- Comprehensive error handling
- Detailed logging

## Requirements

- Python 3.12+
- FastAPI
- PDFPlumber
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd seu-gosi
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create and configure `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Usage

1. Start the server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

2. Access the API documentation:
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Security

- All endpoints require authentication except /docs and /redoc
- IP address restrictions can be configured
- Environment variables for sensitive data
- Secure file handling
- Rate limiting

## License

[License Type] - See LICENSE file for details 