import json
import time
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from authentication.models import APIToken, ProcessingHistory
from apis.models import CertificateUpload
from apis.utils import get_requester_name
from .models import APIEndpointRequest

logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view."""
    template_name = 'dashboard.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        """Get dashboard context data."""
        context = super().get_context_data(**kwargs)
        
        # Get current user
        current_user = self.request.user
        
        # Get user statistics
        user_history = ProcessingHistory.objects.filter(user=current_user)
        user_tokens = APIToken.objects.filter(user=current_user, is_active=True)
        
        stats = {
            'total_requests': user_history.count(),
            'successful_requests': user_history.filter(status='success').count(),
            'failed_requests': user_history.filter(status='error').count(),
            'total_tokens': user_tokens.count(),
        }
        
        # Get recent history (last 5 items)
        recent_history_records = user_history.order_by('-created_at')[:5]
        
        # Process recent history to include formatted data
        recent_history = []
        for record in recent_history_records:
            # Create formatted record
            formatted_record = {
                'id': record.id, # type: ignore
                'requester': record.requester or 'N/A',
                'endpoint': record.endpoint,
                'status': record.status,
                'created_at': record.created_at,
                'processing_time': record.processing_time,
                'error_message': record.error_message,
            }
            
            # Format result for display
            if record.status == 'success' and record.result:
                try:
                    result_data = json.loads(record.result)
                    months = result_data.get('subscription_months', 'N/A')
                    formatted_record['result_summary'] = f"{months} months"
                except (json.JSONDecodeError, TypeError):
                    formatted_record['result_summary'] = 'Processed'
            else:
                formatted_record['result_summary'] = record.error_message or 'Failed'
            
            recent_history.append(formatted_record)
        
        # Calculate processing charts data (moved from ProcessingChartsAPIView)
        total_count = user_history.count()
        success_count = user_history.filter(status='success').count()
        error_count = user_history.filter(status='error').count()
        
        # Calculate API health percentage
        api_health_percentage = 0
        if total_count > 0:
            api_health_percentage = round((success_count / total_count) * 100)
        
        # Calculate processing method statistics
        ai_count = 0
        standard_count = 0
        
        for record in user_history.filter(status='success'):
            if record.result:
                try:
                    result_data = json.loads(record.result)
                    method = result_data.get('processing_method', 'standard')
                    if method == 'ai':
                        ai_count += 1
                    else:
                        standard_count += 1
                except:
                    standard_count += 1
        
        # Get activity over time (last 30 days)
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_history_for_charts = user_history.filter(created_at__gte=thirty_days_ago).order_by('created_at')
        
        # Group by day
        activity_data = {}
        for record in recent_history_for_charts:
            date_key = record.created_at.strftime('%Y-%m-%d')
            if date_key not in activity_data:
                activity_data[date_key] = {'success': 0, 'error': 0}
            activity_data[date_key][record.status] += 1
        
        # Convert to chart data format
        dates = sorted(activity_data.keys())
        success_series = [activity_data[date]['success'] for date in dates]
        error_series = [activity_data[date]['error'] for date in dates]
        
        # Processing charts data for templates
        processing_charts = {
            'processing_stats': {
                'success': success_count,
                'error': error_count,
                'total': total_count
            },
            'processing_methods': {
                'ai': ai_count,
                'standard': standard_count
            },
            'activity_over_time': {
                'dates': dates,
                'success': success_series,
                'error': error_series
            },
            'api_health': {
                'success_percentage': api_health_percentage
            }
        }
        
        context.update({
            'current_user': current_user,
            'stats': stats,
            'recent_history': recent_history,
            'processing_charts': processing_charts,
        })
        
        return context


class LoginPageView(TemplateView):
    """Login page view."""
    template_name = 'login.html'
    
    def get(self, request):
        """Display login page."""
        if request.user.is_authenticated:
            return redirect('web:dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        """Handle login form submission."""
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, self.template_name)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                next_url = request.GET.get('next', '/')
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is disabled.')
        else:
            messages.error(request, 'Invalid username or password.')
        
        return render(request, self.template_name)


class LogoutPageView(View):
    """Logout page view."""
    def get(self, request):
        username = request.user.username if request.user.is_authenticated else None
        logout(request)
        if username:
            messages.success(request, f'Goodbye, {username}!')
        return redirect('web:login')


class ProcessView(LoginRequiredMixin, TemplateView):
    """Certificate processing view."""
    template_name = 'process.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        """Get context data for the process view."""
        context = super().get_context_data(**kwargs)
        
        # Get current user
        current_user = self.request.user
        
        context.update({
            'current_user': current_user,
        })
        
        # Check if there's a processing result in session
        processing_result = self.request.session.get('processing_result')
        if processing_result:
            context['processing_result'] = processing_result
            context['processing_filename'] = self.request.session.get('processing_filename')
            context['processing_time'] = self.request.session.get('processing_time')
            
            # Clear the session data after displaying
            del self.request.session['processing_result']
            if 'processing_filename' in self.request.session:
                del self.request.session['processing_filename']
            if 'processing_time' in self.request.session:
                del self.request.session['processing_time']
        
        return context


class ProcessUploadView(LoginRequiredMixin, View):
    """Process upload view."""
    login_url = '/login/'

    def post(self, request):
        """Handle certificate upload and processing."""
        start_time = time.time()
        endpoint = None  # Initialize endpoint variable
        
        if 'file' not in request.FILES:
            messages.error(request, 'No file provided')
            return redirect('web:process')
        
        uploaded_file = request.FILES['file']
        processing_type = request.POST.get('processing_type', 'standard')
        
        # Get file extension
        file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
        supported_extensions = ['pdf', 'png', 'jpg', 'jpeg']
        
        # Validate file type
        if file_extension not in supported_extensions:
            messages.error(request, 'Please select a PDF or image file (PNG, JPG, JPEG)')
            return redirect('web:process')
        
        # Force AI processing for image files
        if file_extension in ['png', 'jpg', 'jpeg']:
            processing_type = 'ai'
        
        # Validate file size (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            messages.error(request, 'File size must be less than 10MB')
            return redirect('web:process')
        
        try:
            # Create a test client to make internal API calls
            client = Client()
            
            # Prepare the file for API call
            uploaded_file.seek(0)  # Reset file pointer
            file_data = {
                'file': uploaded_file
            }
            
            # Determine API endpoint based on processing type
            if processing_type == 'ai':
                api_url = '/api/v1/AI_extract-GOSI_subscription/'
                endpoint = "/api/v1/AI_extract-GOSI_subscription/"
            else:
                # Standard processing only works with PDF files
                if file_extension != 'pdf':
                    messages.error(request, 'Image files can only be processed with AI processing')
                    return redirect('web:process')
                
                api_url = '/api/v1/extract-GOSI_subscription/'
                endpoint = "/api/v1/extract-GOSI_subscription/"
            
            # Make API call with user authentication
            client.force_login(request.user)
            api_response = client.post(api_url, file_data, format='multipart')
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            if api_response.status_code == 200:
                # Parse the API response
                result = api_response.json()
                
                # Add processing method to result
                result['processing_method'] = processing_type
                
                # Create processing history record for success
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint=endpoint,
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
                    processing_type=processing_type,
                    status="completed",
                    result=json.dumps(result)
                )
                
                # Store result in session for display
                request.session['processing_result'] = result
                request.session['processing_filename'] = uploaded_file.name
                request.session['processing_time'] = f"{processing_time:.2f}"
                
                messages.success(request, f'Certificate processed successfully! Found {result.get("subscription_months", 0)} subscription months.')
                return redirect('web:process')
            else:
                # Handle API error response
                try:
                    error_data = api_response.json()
                    error_message = error_data.get('error', 'Unknown API error')
                    if 'detail' in error_data:
                        error_message = error_data['detail'].get('message', error_message)
                except:
                    error_message = f'API call failed with status {api_response.status_code}'
                
                # Create processing history record for error
                ProcessingHistory.objects.create(
                    user=request.user,
                    endpoint=endpoint,
                    processing_time=f"{processing_time:.2f}",
                    result=None,
                    status='error',
                    error_message=error_message,
                    requester=get_requester_name(request)
                )
                
                messages.error(request, f'Processing failed: {error_message}')
                return redirect('web:process')
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            # Create processing history record for error
            ProcessingHistory.objects.create(
                user=request.user,
                endpoint=endpoint or "/web/process/upload/ (Error)",
                processing_time=f"{processing_time:.2f}",
                result=None,
                status='error',
                error_message=error_message,
                requester=get_requester_name(request)
            )
            
            logger.error(f"Error processing certificate: {error_message}")
            messages.error(request, f'Processing failed: {error_message}')
            return redirect('web:process')


class ProcessResultView(LoginRequiredMixin, TemplateView):
    """Process result view."""
    template_name = 'process_result.html'
    login_url = '/login/'


class TokensView(LoginRequiredMixin, TemplateView):
    """Tokens management view."""
    template_name = 'tokens.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        """Get tokens context data."""
        context = super().get_context_data(**kwargs)
        
        # Get current user
        current_user = self.request.user
        
        # Get user tokens
        user_tokens = APIToken.objects.filter(user=current_user).order_by('-created_at')
        
        # Get API-related processing history (excluding web interface calls)
        api_history = ProcessingHistory.objects.filter(
            user=current_user,
            endpoint__icontains='/api/'
        )
        
        # Calculate time 24 hours ago
        yesterday = timezone.now() - timezone.timedelta(hours=24)
        
        # Calculate token stats
        active_tokens_count = user_tokens.filter(is_active=True, expires_at__gt=timezone.now()).count()
        token_stats = {
            'total_tokens': user_tokens.count(),
            'active_tokens': active_tokens_count,
            'expired_tokens': user_tokens.filter(expires_at__lt=timezone.now()).count() if user_tokens.exists() else 0,
            'inactive_tokens': user_tokens.count() - active_tokens_count if user_tokens.exists() else 0,
            'total_requests': api_history.count(),
            'recent_requests': api_history.filter(created_at__gte=yesterday).count(),
            'expiring_soon': user_tokens.filter(
                expires_at__lt=timezone.now() + timezone.timedelta(days=7),
                is_active=True
            ).count() if user_tokens.exists() else 0,
        }
        
        # Check for new token in session
        new_token = self.request.session.get('new_token')
        if new_token:
            context['new_token'] = new_token
            # Clear the session data after displaying
            del self.request.session['new_token']
        
        context.update({
            'current_user': current_user,
            'user_tokens': user_tokens,
            'token_stats': token_stats,
        })
        
        return context


class TokenCreateView(LoginRequiredMixin, View):
    """Token creation view."""
    login_url = '/login/'
    
    def post(self, request):
        """Handle token creation."""
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            expires_days = request.POST.get('expires_days', '90')
            
            # Validate token name
            if not name:
                messages.error(request, 'Token name is required.')
                return redirect('web:tokens')
            
            # Calculate expiration date
            if expires_days == '0':
                # Never expires
                expires_at = timezone.now() + timezone.timedelta(days=365*10)  # 10 years from now
            else:
                expires_at = timezone.now() + timezone.timedelta(days=int(expires_days))
            
            # Create the token
            token = APIToken.objects.create(
                user=request.user,
                name=name,
                expires_at=expires_at,
                is_active=True
            )
            
            # Store token in session for display (only once)
            request.session['new_token'] = {
                'token': token.token,
                'name': token.name,
                'expires_at': token.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            messages.success(request, f'Token "{name}" created successfully!')
            return redirect('web:tokens')
            
        except Exception as e:
            logger.error(f"Error creating token: {str(e)}")
            messages.error(request, f'Failed to create token: {str(e)}')
            return redirect('web:tokens')


class TokenRevokeView(LoginRequiredMixin, View):
    """Token revocation view."""
    login_url = '/login/'
    
    def post(self, request, pk):
        """Handle token revocation."""
        try:
            # Get the token belonging to the current user
            token = APIToken.objects.get(pk=pk, user=request.user)
            
            # Revoke the token
            token.is_active = False
            token.save()
            
            messages.success(request, f'Token "{token.name}" has been revoked successfully!')
            
        except APIToken.DoesNotExist:
            messages.error(request, 'Token not found or access denied.')
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            messages.error(request, f'Failed to revoke token: {str(e)}')
        
        return redirect('web:tokens')


class HistoryView(LoginRequiredMixin, TemplateView):
    """Processing history view."""
    template_name = 'history.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        """Get history context data."""
        context = super().get_context_data(**kwargs)
        
        # Get current user
        current_user = self.request.user
        
        # Get user processing history
        history_records = ProcessingHistory.objects.filter(user=current_user).order_by('-created_at')
        
        # Parse JSON results for better display
        processed_history = []
        for record in history_records:
            # Create a copy of the record with additional parsed data
            record_data = {
                'id': record.id, # type: ignore
                'created_at': record.created_at,
                'requester': record.requester or 'N/A',
                'processing_time': record.processing_time,
                'status': record.status,
                'endpoint': record.endpoint,
                'error_message': record.error_message,
                'raw_result': record.result,
            }
            
            # Parse JSON result if it exists
            if record.result:
                try:
                    import json
                    result_data = json.loads(record.result)
                    record_data['subscription_months'] = result_data.get('subscription_months', 'N/A')
                    record_data['subscription_years'] = result_data.get('subscription_years', None)
                    record_data['processing_method'] = result_data.get('processing_method', 'Standard')
                except (json.JSONDecodeError, TypeError):
                    record_data['subscription_months'] = 'Parse Error'
                    record_data['subscription_years'] = None
            else:
                record_data['subscription_months'] = 'N/A'
                record_data['subscription_years'] = None
            
            processed_history.append(record_data)
        
        # Calculate stats
        history_stats = {
            'total_records': len(processed_history),
            'successful_records': len([r for r in processed_history if r['status'] == 'success']),
            'failed_records': len([r for r in processed_history if r['status'] == 'error']),
        }
        
        context.update({
            'current_user': current_user,
            'history': processed_history,
            'history_stats': history_stats,
        })
        
        return context


class HistoryDetailView(LoginRequiredMixin, TemplateView):
    """History detail view."""
    template_name = 'history_detail.html'
    login_url = '/login/'


class HistoryDownloadView(LoginRequiredMixin, View):
    """History download view for individual results."""
    login_url = '/login/'
    
    def get(self, request, pk):
        """Download processing result as JSON file."""
        try:
            # Get the processing history record for the current user
            record = ProcessingHistory.objects.get(pk=pk, user=request.user)
            
            # Only allow downloading successful results
            if record.status != 'success' or not record.result:
                messages.error(request, 'No downloadable result available for this record.')
                return redirect('web:history')
            
            # Parse the result data
            try:
                result_data = json.loads(record.result)
            except (json.JSONDecodeError, TypeError):
                messages.error(request, 'Unable to parse result data.')
                return redirect('web:history')
            
            # Create comprehensive download data
            download_data = {
                'processing_info': {
                    'id': record.id, # type: ignore
                    'processing_time_seconds': record.processing_time,
                    'processed_at': record.created_at.isoformat(),
                    'endpoint': record.endpoint,
                    'status': record.status
                },
                'result': result_data,
                'metadata': {
                    'downloaded_at': timezone.now().isoformat(),
                    'downloaded_by': request.user.username,
                    'seu_tools_version': '1.0.0'
                }
            }
            
            # Create JSON response with download headers
            response = JsonResponse(download_data, json_dumps_params={'indent': 2})
            
            # Set headers to trigger download
            filename = f"seu_tools_result_{record.id}.json" # type: ignore
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Type'] = 'application/json'
            
            return response
            
        except ProcessingHistory.DoesNotExist:
            messages.error(request, 'Processing record not found or access denied.')
            return redirect('web:history')
        except Exception as e:
            logger.error(f"Error downloading result: {str(e)}")
            messages.error(request, f'Failed to download result: {str(e)}')
            return redirect('web:history')


class HistoryExportView(LoginRequiredMixin, View):
    """History export view."""
    login_url = '/login/'
    
    def get(self, request):
        """Export user's processing history as CSV file."""
        try:
            import csv
            from django.http import HttpResponse
            from io import StringIO
            from datetime import datetime
            
            # Get current user's processing history
            current_user = request.user
            history_query = ProcessingHistory.objects.filter(user=current_user)
            
            # Apply filters from query parameters
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            status_filter = request.GET.get('status')
            
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                    history_query = history_query.filter(created_at__date__gte=from_date)
                except ValueError:
                    pass  # Invalid date format, ignore filter
            
            if date_to:
                try:
                    to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                    history_query = history_query.filter(created_at__date__lte=to_date)
                except ValueError:
                    pass  # Invalid date format, ignore filter
            
            if status_filter and status_filter in ['success', 'error']:
                history_query = history_query.filter(status=status_filter)
            
            history_records = history_query.order_by('-created_at')
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            
            # Generate filename with filter info
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filter_suffix = ""
            
            if date_from or date_to or status_filter:
                filter_parts = []
                if date_from: filter_parts.append(f"from_{date_from}")
                if date_to: filter_parts.append(f"to_{date_to}")
                if status_filter: filter_parts.append(f"{status_filter}_only")
                filter_suffix = f"_filtered_{'_'.join(filter_parts)}"
            
            filename = f"seu_tools_history_{current_user.username}_{timestamp}{filter_suffix}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Create CSV writer
            writer = csv.writer(response)
            
            # Write CSV headers
            writer.writerow([
                'ID',
                'Date',
                'Time',
                'Processing Time (seconds)',
                'Endpoint',
                'Status',
                'Subscription Months',
                'Subscription Years',
                'Processing Method',
                'Error Message'
            ])
            
            # Write data rows and collect statistics
            total_records = 0
            success_count = 0
            error_count = 0
            ai_processing_count = 0
            standard_processing_count = 0
            
            for record in history_records:
                total_records += 1
                
                # Count status
                if record.status == 'success':
                    success_count += 1
                else:
                    error_count += 1
                
                # Parse result data if available
                subscription_months = 'N/A'
                subscription_years = 'N/A'
                processing_method = 'Standard'
                
                if record.result:
                    try:
                        result_data = json.loads(record.result)
                        subscription_months = result_data.get('subscription_months', 'N/A')
                        subscription_years = result_data.get('subscription_years', 'N/A')
                        processing_method = result_data.get('processing_method', 'Standard')
                        
                        # Count processing methods
                        if processing_method.lower() == 'ai':
                            ai_processing_count += 1
                        else:
                            standard_processing_count += 1
                            
                    except (json.JSONDecodeError, TypeError):
                        subscription_months = 'Parse Error'
                        subscription_years = 'Parse Error'
                        standard_processing_count += 1
                else:
                    standard_processing_count += 1
                
                writer.writerow([
                    record.id, # type: ignore
                    record.created_at.strftime('%Y-%m-%d'),
                    record.created_at.strftime('%H:%M:%S'),
                    record.processing_time,
                    record.endpoint,
                    record.status.title(),
                    subscription_months,
                    subscription_years,
                    processing_method.title(),
                    record.error_message or ''
                ])
            
            # Add summary section
            if total_records > 0:
                writer.writerow([])  # Empty row for separation
                writer.writerow(['SUMMARY'])
                writer.writerow(['Total Records', total_records])
                writer.writerow(['Successful', success_count])
                writer.writerow(['Failed', error_count])
                writer.writerow(['AI Processing', ai_processing_count])
                writer.writerow(['Standard Processing', standard_processing_count])
                writer.writerow(['Export Date', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Exported By', current_user.username])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting history: {str(e)}")
            messages.error(request, f'Failed to export history: {str(e)}')
            return redirect('web:history')



class APIRequestListView(LoginRequiredMixin, TemplateView):
    """View for listing API endpoint requests."""
    template_name = 'api_requests.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        
        # Get requests based on user role
        if current_user.is_staff: # type: ignore
            requests = APIEndpointRequest.objects.all()
            
        else:
            requests = APIEndpointRequest.objects.filter(user=current_user)
        
        context.update({
            'current_user': current_user,
            'api_requests': requests,
        })
        
        return context


class APIRequestCreateView(LoginRequiredMixin, View):
    """View for creating new API endpoint requests (AJAX only)."""
    login_url = '/login/'
    
    def get(self, request):
        # This view only handles AJAX requests now
        return JsonResponse({'status': 'error', 'message': 'This endpoint only supports AJAX requests'}, status=400)
    
    def post(self, request):
        try:
            # Create new request
            api_request = APIEndpointRequest.objects.create(
                user=request.user,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                endpoint_path=request.POST.get('endpoint_path'),
                http_method=request.POST.get('http_method'),
                expected_input=request.POST.get('expected_input'),
                expected_output=request.POST.get('expected_output'),
                business_justification=request.POST.get('business_justification', ''),
                use_case=request.POST.get('use_case', ''),
                priority=request.POST.get('priority'),
                date_needed=request.POST.get('date_needed'),
                requester=request.POST.get('requester', request.user.username)
            )
            
            # Handle admin fields if user is staff
            if request.user.is_staff:
                api_request.status = request.POST.get('status', 'pending')
                api_request.admin_notes = request.POST.get('admin_notes', '')
                api_request.developed_endpoint_url = request.POST.get('developed_endpoint_url', '')
                api_request.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Request created successfully'})
            else:
                # Fallback for non-AJAX requests
                messages.success(request, 'API endpoint request submitted successfully!')
                return redirect('web:api_requests')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            else:
                messages.error(request, f'Error creating request: {str(e)}')
                return redirect('web:api_requests')


class APIRequestDetailView(LoginRequiredMixin, View):
    """View for viewing API endpoint request details (AJAX only)."""
    login_url = '/login/'
    
    def get(self, request, pk):
        try:
            api_request = APIEndpointRequest.objects.get(pk=pk)
            # Check if user has access
            if not request.user.is_staff and api_request.user != request.user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
                else:
                    messages.error(request, 'Access denied.')
                return redirect('web:api_requests')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return JSON data for AJAX requests
                data = {
                    'id': api_request.pk,
                    'title': api_request.title,
                    'description': api_request.description,
                    'endpoint_path': api_request.endpoint_path,
                    'http_method': api_request.http_method,
                    'method_class': self._get_method_class(api_request.http_method),
                    'expected_input': api_request.expected_input,
                    'expected_output': api_request.expected_output,
                    'business_justification': api_request.business_justification,
                    'use_case': api_request.use_case,
                    'priority': api_request.priority,
                    'priority_class': self._get_priority_class(api_request.priority),
                    'date_needed': api_request.date_needed.strftime('%Y-%m-%d'),
                    'status': api_request.status,
                    'status_display': api_request.get_status_display(), # type: ignore
                    'status_class': self._get_status_class(api_request.status),
                    'requester': api_request.requester,
                    'created_at': api_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': api_request.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_staff': request.user.is_staff,
                    'can_edit': request.user.is_staff or api_request.user == request.user,
                }
                
                if request.user.is_staff:
                    data.update({
                        'admin_notes': api_request.admin_notes,
                        'developed_endpoint_url': api_request.developed_endpoint_url,
                    })
                
                return JsonResponse(data)
            else:
                # Fallback for non-AJAX requests
                messages.info(request, 'This view only supports AJAX requests. Please use the main API requests page.')
                return redirect('web:api_requests')
                
        except APIEndpointRequest.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Request not found'}, status=404)
            else:
                messages.error(request, 'Request not found.')
            return redirect('web:api_requests')
        
    def _get_method_class(self, method):
        """Get Bootstrap class for HTTP method badge."""
        return {
            'GET': 'bg-success',
            'POST': 'bg-primary',
            'PUT': 'bg-warning',
            'PATCH': 'bg-info',
            'DELETE': 'bg-danger'
        }.get(method, 'bg-secondary')
    
    def _get_priority_class(self, priority):
        """Get Bootstrap class for priority badge."""
        return {
            'critical': 'bg-danger',
            'high': 'bg-warning',
            'medium': 'bg-info',
            'low': 'bg-secondary'
        }.get(priority, 'bg-secondary')
    
    def _get_status_class(self, status):
        """Get Bootstrap class for status badge."""
        return {
            'completed': 'bg-success',
            'in_progress': 'bg-warning',
            'rejected': 'bg-danger',
            'pending': 'bg-secondary'
        }.get(status, 'bg-secondary')


class APIRequestUpdateView(LoginRequiredMixin, View):
    """View for updating API endpoint requests (AJAX only)."""
    login_url = '/login/'
    
    def get(self, request, pk):
        # This view only handles AJAX requests now
        return JsonResponse({'status': 'error', 'message': 'This endpoint only supports AJAX requests'}, status=400)
    
    def post(self, request, pk):
        try:
            api_request = APIEndpointRequest.objects.get(pk=pk)
            if not request.user.is_staff and api_request.user != request.user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
                else:
                    messages.error(request, 'Access denied.')
                return redirect('web:api_requests')
            
            # Update fields
            api_request.title = request.POST.get('title')
            api_request.description = request.POST.get('description')
            api_request.endpoint_path = request.POST.get('endpoint_path')
            api_request.http_method = request.POST.get('http_method')
            api_request.expected_input = request.POST.get('expected_input')
            api_request.expected_output = request.POST.get('expected_output')
            api_request.business_justification = request.POST.get('business_justification', '')
            api_request.use_case = request.POST.get('use_case', '')
            api_request.priority = request.POST.get('priority')
            api_request.date_needed = request.POST.get('date_needed')
            api_request.requester = request.POST.get('requester', request.user.username)
            
            # Handle admin fields if user is staff
            if request.user.is_staff:
                api_request.status = request.POST.get('status', api_request.status)
                api_request.admin_notes = request.POST.get('admin_notes', api_request.admin_notes)
                api_request.developed_endpoint_url = request.POST.get('developed_endpoint_url', api_request.developed_endpoint_url)
            
            api_request.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Request updated successfully'})
            else:
                # Fallback for non-AJAX requests
                messages.success(request, 'API endpoint request updated successfully!')
                return redirect('web:api_requests')
            
        except APIEndpointRequest.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Request not found'}, status=404)
            else:
                messages.error(request, 'Request not found.')
            return redirect('web:api_requests')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            else:
                messages.error(request, f'Error updating request: {str(e)}')
                return redirect('web:api_requests')
