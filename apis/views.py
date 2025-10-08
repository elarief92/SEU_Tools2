import json
import time
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.reverse import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.db import connection
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import CertificateUpload, APIEndpoint
from .serializers import APIEndpointSerializer
from .utils import extract_subscription_months_from_pdf, extract_subscription_months_with_ai, get_requester_name
from authentication.views import  APITokenAuthentication
from authentication.models import ProcessingHistory

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([])  # Allow anonymous access
def api_root(request, format=None):
    """
    Dynamic API root endpoint showing all available endpoints.
    """
    return Response({
        'message': 'SEU Tools API',
        'version': 'v1',
        'endpoints': {
            'extract-GOSI_subscription': reverse('extract-GOSI_subscription', request=request, format=format),
            'AI_extract-GOSI_subscription': reverse('AI_extract-GOSI_subscription', request=request, format=format),
            'get-student-transcript': reverse('get-student-transcript', request=request, format=format),
            'student-info': reverse('student-info', request=request, format=format),
            'process-certificate': reverse('process-certificate', request=request, format=format),
        },
        'documentation': {
            'swagger': request.build_absolute_uri('/docs/'),
            'redoc': request.build_absolute_uri('/redoc/'),
        }
    })

class APIEndpointViewSet(viewsets.ModelViewSet):
    serializer_class = APIEndpointSerializer
    authentication_classes = [APITokenAuthentication,  SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff: # type: ignore
            return APIEndpoint.objects.all()
        return APIEndpoint.objects.filter(user=self.request.user)

@method_decorator(csrf_exempt, name='dispatch')
class ExtractSubscriptionMonthsView(APIView):
    """
    Extract total subscription months from a certificate PDF using standard text extraction.
    
    This endpoint processes both Arabic and English GOSI certificates to extract
    the total subscription months value using direct PDF text extraction.
    """
    parser_classes = [MultiPartParser]  # Let DRF use default parsers
    authentication_classes = [APITokenAuthentication,  SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Extract subscription months from PDF",
        operation_description="""
        Extract total subscription months from a GOSI certificate PDF using standard text extraction.
        
        This endpoint processes both Arabic and English GOSI certificates to extract
        the total subscription months value using direct PDF text extraction.
        
        **File Requirements:**
        - File format: PDF only
        - Maximum file size: 10MB
        - Supported languages: Arabic, English
        """,
        # consumes=['multipart/form-data'],
        manual_parameters=[
            openapi.Parameter(
                'file',
                openapi.IN_FORM,
                description="PDF file containing the GOSI certificate",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Success - Subscription months extracted",
                examples={
                    "application/json": {
                        "status": "success",
                        "subscription_months": 24,
                        "subscription_years": 2,
                        "processing_method": "standard",
                        "filename": "certificate.pdf"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Invalid file or missing file",
                examples={
                    "application/json": {
                        "error": "No file provided"
                    }
                }
            ),
            404: openapi.Response(
                description="Not Found - Could not extract subscription months",
                examples={
                    "application/json": {
                        "detail": {
                            "message": "Could not find subscription months in the certificate",
                            "debug_text": ["Extracted text samples..."]
                        }
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error",
                examples={
                    "application/json": {
                        "error": "Processing failed"
                    }
                }
            )
        },
        tags=['Certificate Processing']
    )
    def post(self, request, *args, **kwargs):
        start_time = time.time()
        
        if 'file' not in request.FILES:
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/extract-GOSI_subscription/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="No file provided",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        if not uploaded_file.name.lower().endswith('.pdf'):
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/extract-GOSI_subscription/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="Only PDF files are supported",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "Only PDF files are supported"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/extract-GOSI_subscription/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="File size must be less than 10MB",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "File size must be less than 10MB"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read file content
            file_content = uploaded_file.read()
            
            # Process the PDF
            result = extract_subscription_months_from_pdf(file_content, uploaded_file.name)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            if result["status"] == "success":
                # Create processing history record
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/extract-GOSI_subscription/",
                    processing_time=f"{processing_time:.2f}",
                    result=json.dumps(result),
                    status='success',
                    requester=get_requester_name(request)
                )
                
                # Create certificate upload record
                CertificateUpload.objects.create(
                    user=request.user,
                    filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    processing_type="standard",
                    status="completed"
                )
                
                return Response(result, status=status.HTTP_200_OK)
            else:
                # Create processing history record for error
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/extract-GOSI_subscription/",
                    processing_time=f"{processing_time:.2f}",
                    result=None,
                    status='error',
                    error_message=result.get("error_message", "Unknown error"),
                    requester=get_requester_name(request)
                )
                
                return Response(
                    {"detail": {
                        "message": result.get("error_message", "Unknown error"),
                        "debug_text": result.get("debug_text", [])
                    }},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            # Create processing history record for error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/extract-GOSI_subscription/",
                processing_time=f"{processing_time:.2f}",
                result=None,
                status='error',
                error_message=error_message,
                requester=get_requester_name(request)
            )
            
            logger.error(f"Error processing certificate: {error_message}")
            return Response(
                {"error": error_message}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class ExtractSubscriptionMonthsByAIView(APIView):
    """
    Extract total subscription months from a certificate using AI analysis.
    
    This endpoint processes both PDF and image files using Azure OpenAI's vision model
    to extract subscription months information from GOSI certificates.
    """
    parser_classes = [MultiPartParser]  # Let DRF use default parsers
    authentication_classes = [APITokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Extract subscription months using AI",
        operation_description="""
        Extract total subscription months from a GOSI certificate using AI-powered analysis.
        
        This endpoint processes both PDF and image files using Azure OpenAI's vision model
        to extract subscription months information from GOSI certificates.
        
        **File Requirements:**
        - File formats: PDF, PNG, JPG, JPEG, GIF, BMP, TIFF
        - Maximum file size: 10MB
        - Supported languages: Arabic, English
        
        **AI Processing:**
        - Uses Azure OpenAI vision model for analysis
        - More accurate for complex or damaged certificates
        - Handles both text and image-based certificates
        """,
        # consumes=['multipart/form-data'],
        manual_parameters=[
            openapi.Parameter(
                'file',
                openapi.IN_FORM,
                description="Certificate file (PDF or image format)",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Success - Subscription months extracted using AI",
                examples={
                    "application/json": {
                        "status": "success",
                        "subscription_months": 36,
                        "subscription_years": 3,
                        "processing_method": "ai",
                        "filename": "certificate.jpg",
                        "ai_confidence": "high"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Invalid file or unsupported format",
                examples={
                    "application/json": {
                        "error": "Supported file types: PDF, PNG, JPG, JPEG, GIF, BMP, TIFF"
                    }
                }
            ),
            404: openapi.Response(
                description="Not Found - Could not extract subscription months",
                examples={
                    "application/json": {
                        "detail": {
                            "message": "Could not find subscription months in the certificate",
                            "ai_analysis": "Certificate appears to be invalid or corrupted"
                        }
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error - AI processing failed",
                examples={
                    "application/json": {
                        "error": "AI processing failed"
                    }
                }
            )
        },
        tags=['Certificate Processing']
    )
    def post(self, request, *args, **kwargs):
        start_time = time.time()
        
        if 'file' not in request.FILES:
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/AI_extract-GOSI_subscription/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="No file provided",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_types = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
        if not any(uploaded_file.name.lower().endswith(ext) for ext in allowed_types):
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/AI_extract-GOSI_subscription/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="Supported file types: PDF, PNG, JPG, JPEG, GIF, BMP, TIFF",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "Supported file types: PDF, PNG, JPG, JPEG, GIF, BMP, TIFF"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/AI_extract-GOSI_subscription/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="File size must be less than 10MB",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "File size must be less than 10MB"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read file content
            file_content = uploaded_file.read()
            
            # Track processing start time
            processing_start_time = time.time()
            
            # Process the file with AI
            result = extract_subscription_months_with_ai(
                file_content, 
                uploaded_file.name, 
                uploaded_file.content_type
            )
            
            # Calculate processing time
            processing_end_time = time.time()
            processing_time = processing_end_time - processing_start_time
            total_time = processing_end_time - start_time
            
            if result["status"] == "success":
                # Add timing information to the response
                # result["processing_time_seconds"] = f"{processing_time:.2f}"
                # result["total_time_seconds"] = f"{total_time:.2f}"
                
                # Create processing history record
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/AI_extract-GOSI_subscription/",
                    processing_time=f"{processing_time:.2f}",
                    result=json.dumps(result),
                    status='success',
                    requester=get_requester_name(request)
                )
                
                # Create certificate upload record
                CertificateUpload.objects.create(
                    user=request.user,
                    filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    processing_type="ai",
                    status="completed"
                )
                
                return Response(result, status=status.HTTP_200_OK)
            else:
                # Create processing history record for error
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/AI_extract-GOSI_subscription/",
                    processing_time=f"{processing_time:.2f}",
                    result=None,
                    status='error',
                    error_message=result.get("error_message", "Unknown error"),
                    requester=get_requester_name(request)
                )
                
                return Response(
                    {"error": result.get("error_message", "Unknown error")},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            # Create processing history record for error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/AI_extract-GOSI_subscription/",
                processing_time=f"{processing_time:.2f}",
                result=None,
                status='error',
                error_message=error_message,
                requester=get_requester_name(request)
            )
            
            logger.error(f"Error processing certificate with AI: {error_message}")
            return Response(
                {"error": error_message}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@authentication_classes([APITokenAuthentication,  SessionAuthentication])
@permission_classes([IsAuthenticated])
def process_certificate(request):
    """
    Process certificate endpoint.
    """
    start_time = time.time()
    
    if 'file' not in request.FILES:
        # Create processing history record for validation error
        ProcessingHistory.objects.create(
            user=request.user,
            endpoint="/api/process-certificate/",
            processing_time=f"{time.time() - start_time:.2f}",
            result=None,
            status='error',
            error_message="No file provided",
            requester=get_requester_name(request)
        )
        return Response(
            {"error": "No file provided"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    
    try:
        # Process the file
        result = extract_subscription_months_from_pdf(uploaded_file.read(), uploaded_file.name)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        if result.get("status") == "success":
            # Create processing history record for success
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/process-certificate/",
                processing_time=f"{processing_time:.2f}",
                result=json.dumps(result),
                status='success',
                requester=get_requester_name(request)
            )
        else:
            # Create processing history record for processing error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/process-certificate/",
                processing_time=f"{processing_time:.2f}",
                result=None,
                status='error',
                error_message=result.get("error_message", "Processing failed"),
                requester=get_requester_name(request)
            )
        
        return Response(result)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = str(e)
        
        # Create processing history record for exception
        ProcessingHistory.objects.create(
            user=request.user,
            endpoint="/api/process-certificate/",
            processing_time=f"{processing_time:.2f}",
            result=None,
            status='error',
            error_message=error_message,
            requester=get_requester_name(request)
        )
        
        logger.error(f"Error in process_certificate: {error_message}")
        return Response(
            {"error": error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@method_decorator(csrf_exempt, name='dispatch')
class GetStudentTranscriptView(APIView):
    """
    Get student transcript data from Banner system.
    
    This endpoint retrieves student transcript information from the Banner system
    using SQL queries and returns the result in JSON format.
    """
    authentication_classes = [APITokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get student transcript from Banner system",
        operation_description="""
        Retrieve student transcript data from the Banner system using the student ID.
        
        This endpoint executes SQL queries against the Banner database to fetch
        comprehensive transcript information including courses, grades, and GPA.
        
        **Parameters:**
        - student_id: The student's ID number (required)
        """,
        manual_parameters=[
            openapi.Parameter(
                'student_id',
                openapi.IN_QUERY,
                description="Student ID number",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Success - Transcript data retrieved",
                examples={
                    "application/json": {
                        "status": "success",
                        "student_id": "1001171212",
                        "student_name": "John Doe",
                        "transcript_data": {
                            "courses": [
                                {
                                    "course_code": "CS101",
                                    "course_name": "Introduction to Computer Science",
                                    "credit_hours": 3,
                                    "grade": "A",
                                    "semester": "Fall 2023"
                                }
                            ],
                            "gpa": 3.75,
                            "total_credit_hours": 120
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Missing or invalid student ID",
                examples={
                    "application/json": {
                        "error": "Student ID is required"
                    }
                }
            ),
            404: openapi.Response(
                description="Not Found - Student not found in Banner system",
                examples={
                    "application/json": {
                        "error": "Student not found"
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error - Database connection failed",
                examples={
                    "application/json": {
                        "error": "Database query failed"
                    }
                }
            )
        },
        tags=['Student Services']
    )
    def get(self, request, *args, **kwargs):
        start_time = time.time()
        
        # Get student ID from query parameters
        student_id = request.query_params.get('student_id')
        
        if not student_id:
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/get-student-transcript/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="Student ID is required",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "Student ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if Banner database is available
            from django.db import connections
            from django.conf import settings
            
            if 'banner' not in connections.databases:
                # Banner database not configured
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/get-student-transcript/",
                    processing_time=f"{time.time() - start_time:.2f}",
                    result=None,
                    status='error',
                    error_message="Banner database not configured",
                    requester=get_requester_name(request)
                )
                return Response(
                    {"error": "Student services are currently unavailable"}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Use the academic record service to get comprehensive transcript data
            from .academic_record_service import AcademicRecordService, StudentAcademicInfo, convert_academic_info_to_dict
            
            # First, get the student's PIDM from student_id
            banner_db = connections['banner']
            with banner_db.cursor() as cursor:
                # Get PIDM from student ID
                pidm_query = """
                    SELECT PIDM 
                    FROM STDS_INFO_M 
                    WHERE STD_ID = %s
                """
                cursor.execute(pidm_query, [student_id])
                pidm_row = cursor.fetchone()
                
                if not pidm_row:
                    # Create processing history record for not found
                    ProcessingHistory.objects.create(
                        user=request.user,
                        endpoint="/api/get-student-transcript/",
                        processing_time=f"{time.time() - start_time:.2f}",
                        result=None,
                        status='error',
                        error_message="Student not found",
                        requester=get_requester_name(request)
                    )
                    return Response(
                        {"error": "Student not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                pidm = str(pidm_row[0])
                
                # Create academic info object
                student_academic_info = StudentAcademicInfo(PIDM=pidm)
                
                # Get academic record details using the service
                academic_service = AcademicRecordService()
                academic_service.get_academic_record_details_sync(student_academic_info)
                
                # Convert to dictionary for JSON response
                transcript_data = convert_academic_info_to_dict(student_academic_info)
                
                # Prepare response data
                result = {
                    "status": "success",
                    "student_id": student_id,
                    "pidm": pidm,
                    "transcript_data": transcript_data
                }
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Create processing history record
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/get-student-transcript/",
                    processing_time=f"{processing_time:.2f}",
                    result=json.dumps(result),
                    status='success',
                    requester=get_requester_name(request)
                )
                
                return Response(result, status=status.HTTP_200_OK)
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            # Create processing history record for error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/get-student-transcript/",
                processing_time=f"{processing_time:.2f}",
                result=None,
                status='error',
                error_message=error_message,
                requester=get_requester_name(request)
            )
            
            logger.error(f"Error getting student transcript: {error_message}")
            return Response(
                {"error": "Database query failed"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    


@method_decorator(csrf_exempt, name='dispatch')
class StudentInfoView(APIView):
    """
    Get student information from Banner system.
    
    This endpoint retrieves student basic information from the Banner system
    using SQL queries and returns the result in JSON format.
    """
    authentication_classes = [APITokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get student information from Banner system",
        operation_description="""
        Retrieve student basic information from the Banner system using the student ID.
        
        This endpoint executes SQL queries against the Banner database to fetch
        student information including names, SSN, nationality, college, and major.
        
        **Parameters:**
        - student_id: The student's ID number (required)
        """,
        manual_parameters=[
            openapi.Parameter(
                'student_id',
                openapi.IN_QUERY,
                description="Student ID number",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Success - Student information retrieved",
                examples={
                    "application/json": {
                        "status": "success",
                        "student_info": {
                            "StudentId": "1001171212",
                            "SSN": "1234567890",
                            "EnglishName": "John Doe",
                            "ArabicName": "جون دو",
                            "Name": "جون دو",
                            "PIDM": "12345",
                            "Nationality": "Saudi Arabian",
                            "College": "كلية الهندسة",
                            "Major": "هندسة الحاسب الآلي"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Missing or invalid student ID",
                examples={
                    "application/json": {
                        "error": "Student ID is required"
                    }
                }
            ),
            404: openapi.Response(
                description="Not Found - Student not found in Banner system",
                examples={
                    "application/json": {
                        "error": "Student not found"
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error - Database connection failed",
                examples={
                    "application/json": {
                        "error": "Database query failed"
                    }
                }
            )
        },
        tags=['Student Services']
    )
    def get(self, request, *args, **kwargs):
        start_time = time.time()
        
        
        # Get student ID from query parameters
        student_id = request.query_params.get('student_id')
        
        if not student_id:
            # Create processing history record for validation error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/student-info/",
                processing_time=f"{time.time() - start_time:.2f}",
                result=None,
                status='error',
                error_message="Student ID is required",
                requester=get_requester_name(request)
            )
            return Response(
                {"error": "Student ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if Banner database is available
            from django.db import connections
            from django.conf import settings
            
            if 'banner' not in connections.databases:
                # Banner database not configured
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/student-info/",
                    processing_time=f"{time.time() - start_time:.2f}",
                    result=None,
                    status='error',
                    error_message="Banner database not configured",
                    requester=get_requester_name(request)
                )
                return Response(
                    {"error": "Student services are currently unavailable"}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Execute SQL query to get student information from Banner system
            banner_db = connections['banner']
            print("banner_db", banner_db)
            with banner_db.cursor() as cursor:
                print("cursor", cursor)
                # Define SQL query components
                select_fields = """
                    STD_ID As StudentId,
                    SSN As SSN,
                    FULL_NAME_EN As EnglishName,
                    FULL_NAME_AR As ArabicName,
                    FULL_NAME_AR As Name,
                    PIDM,
                    CITIZIN_DESC As Nationality,
                    c.Coll_Title_AR As College,
                    m.Major_TITle_AR As Major
                """
                
                from_clause = "STDS_INFO_M s, SEU_COLLEGE_M c, SEU_MAJOR_M m"
                
                where_clause = f"s.Std_ID = '{student_id}'"
                
                # Construct the complete SQL query
                sql_query = f"""
                    SELECT {select_fields}
                    FROM {from_clause}
                    WHERE {where_clause}
                """
                print("sql_query", sql_query)
                cursor.execute(sql_query, [student_id])
                row = cursor.fetchone()
                
                if not row:
                    # Create processing history record for not found
                    ProcessingHistory.objects.create(
                        user=request.user,
                        endpoint="/api/student-info/",
                        processing_time=f"{time.time() - start_time:.2f}",
                        result=None,
                        status='error',
                        error_message="Student not found",
                        requester=get_requester_name(request)
                    )
                    return Response(
                        {"error": "Student not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Process the result
                student_info = {
                    "StudentId": row[0],
                    "SSN": row[1],
                    "EnglishName": row[2],
                    "ArabicName": row[3],
                    "Name": row[4],
                    "PIDM": row[5],
                    "Nationality": row[6],
                    "College": row[7],
                    "Major": row[8]
                }
                
                # Prepare response data
                result = {
                    "status": "success",
                    "student_info": student_info
                }
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Create processing history record
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint="/api/student-info/",
                    processing_time=f"{processing_time:.2f}",
                    result=json.dumps(result),
                    status='success',
                    requester=get_requester_name(request)
                )
                
                return Response(result, status=status.HTTP_200_OK)
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            # Create processing history record for error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint="/api/student-info/",
                processing_time=f"{processing_time:.2f}",
                result=None,
                status='error',
                error_message=error_message,
                requester=get_requester_name(request)
            )
            
            logger.error(f"Error getting student info: {error_message}")
            return Response(
                {"error": "Database query failed"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



