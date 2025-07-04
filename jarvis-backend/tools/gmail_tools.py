"""Gmail Tools for Jarvis Backend - Complete implementation matching MCP functionality."""

import os
import json
import base64
import mimetypes
import webbrowser
import urllib.parse
import secrets
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Dict, Any, Optional, Union, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import asyncio
import logging
from datetime import datetime
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email_validator import validate_email, EmailNotValidError
from agents import function_tool

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
GMAIL_CREDENTIALS_DIR = os.path.expanduser("~/.gmail-mcp")
OAUTH_KEYS_FILE = os.path.join(GMAIL_CREDENTIALS_DIR, "gcp-oauth.keys.json")
CREDENTIALS_FILE = os.path.join(GMAIL_CREDENTIALS_DIR, "credentials.json")


class GmailAuthenticationError(Exception):
    """Raised when Gmail authentication fails."""
    pass


class GmailAPIError(Exception):
    """Raised when Gmail API operations fail."""
    pass


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler for OAuth callback"""
    
    def __init__(self, auth_code_container, *args, **kwargs):
        self.auth_code_container = auth_code_container
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request for OAuth callback"""
        # Parse the authorization code from the callback
        url_parts = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(url_parts.query)
        
        if 'code' in query_params:
            self.auth_code_container['code'] = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                    <script>window.close();</script>
                </body>
                </html>
            ''')
        elif 'error' in query_params:
            self.auth_code_container['error'] = query_params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error: {query_params['error'][0]}</h1></body></html>".encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Invalid callback</h1></body></html>")
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


class GmailTools:
    """Gmail Tools class providing all Gmail functionality."""
    
    def __init__(self):
        self.service = None
        self._ensure_credentials_dir()
    
    def _ensure_credentials_dir(self):
        """Ensure credentials directory exists."""
        os.makedirs(GMAIL_CREDENTIALS_DIR, exist_ok=True)
    
    def _custom_oauth_flow(self, oauth_keys: Dict[str, Any]) -> Credentials:
        """Custom OAuth flow that works with both web and installed apps"""
        
        # Extract client configuration
        if 'web' in oauth_keys:
            client_config = oauth_keys['web']
            app_type = 'web'
        elif 'installed' in oauth_keys:
            client_config = oauth_keys['installed']
            app_type = 'installed'
        else:
            raise GmailAuthenticationError("Invalid OAuth configuration")
        
        client_id = client_config['client_id']
        client_secret = client_config['client_secret']
        redirect_uris = client_config.get('redirect_uris', [])
        
        # Find the best redirect URI
        redirect_uri = None
        port = 3000
        
        if app_type == 'web':
            # Use the configured redirect URI from web app
            for uri in redirect_uris:
                if 'localhost' in uri:
                    redirect_uri = uri
                    # Extract port
                    import re
                    port_match = re.search(r'localhost:(\d+)', uri)
                    if port_match:
                        port = int(port_match.group(1))
                    break
            
            if not redirect_uri:
                redirect_uri = redirect_uris[0] if redirect_uris else 'http://localhost:3000/oauth2callback'
        else:
            # For installed apps, use standard localhost
            redirect_uri = 'http://localhost:8080'
            port = 8080
        
        # Generate state for security
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(SCOPES),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        
        auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(auth_params)
        
        print(f"Opening browser for authentication...")
        print(f"Redirect URI: {redirect_uri}")
        print(f"Port: {port}")
        
        # Start local server to receive callback
        auth_code_container = {}
        
        def handler_factory(container):
            def handler(*args, **kwargs):
                return OAuthCallbackHandler(container, *args, **kwargs)
            return handler
        
        try:
            server = HTTPServer(('127.0.0.1', port), handler_factory(auth_code_container))
            
            # Open browser
            webbrowser.open(auth_url)
            
            print(f"Waiting for authorization on http://127.0.0.1:{port}...")
            
            # Wait for callback (timeout after 120 seconds)
            import threading
            import time
            
            def timeout_handler():
                time.sleep(120)
                if 'code' not in auth_code_container and 'error' not in auth_code_container:
                    auth_code_container['timeout'] = True
                    server.shutdown()
            
            timeout_thread = threading.Thread(target=timeout_handler)
            timeout_thread.daemon = True
            timeout_thread.start()
            
            # Handle one request
            server.handle_request()
            server.server_close()
            
            if 'timeout' in auth_code_container:
                raise GmailAuthenticationError("Authentication timed out")
            elif 'error' in auth_code_container:
                raise GmailAuthenticationError(f"Authentication error: {auth_code_container['error']}")
            elif 'code' not in auth_code_container:
                raise GmailAuthenticationError("No authorization code received")
            
            auth_code = auth_code_container['code']
            
        except Exception as e:
            raise GmailAuthenticationError(f"OAuth server error: {e}")
        
        # Exchange authorization code for tokens
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        try:
            response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
            response.raise_for_status()
            token_response = response.json()
            
            # Create credentials object
            credentials_data = {
                'token': token_response['access_token'],
                'refresh_token': token_response.get('refresh_token'),
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': client_id,
                'client_secret': client_secret,
                'scopes': SCOPES
            }
            
            creds = Credentials.from_authorized_user_info(credentials_data, SCOPES)
            return creds
            
        except requests.RequestException as e:
            raise GmailAuthenticationError(f"Token exchange failed: {e}")
        except Exception as e:
            raise GmailAuthenticationError(f"Failed to create credentials: {e}")
    
    async def authenticate(self) -> bool:
        """Authenticate with Gmail API using custom OAuth2 flow."""
        try:
            creds = None
            
            # Load existing credentials
            if os.path.exists(CREDENTIALS_FILE):
                try:
                    creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
                except Exception as e:
                    logger.warning(f"Failed to load existing credentials: {e}")
                    # Remove invalid credentials file
                    os.remove(CREDENTIALS_FILE)
                    creds = None
            
            # If no valid credentials available, request authorization
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Failed to refresh credentials: {e}")
                        creds = None
                
                if not creds:
                    # Check if OAuth keys exist
                    if not os.path.exists(OAUTH_KEYS_FILE):
                        raise GmailAuthenticationError(
                            f"OAuth keys file not found at {OAUTH_KEYS_FILE}. "
                            "Please create this file with your Google OAuth2 credentials."
                        )
                    
                    # Load OAuth keys
                    with open(OAUTH_KEYS_FILE, 'r') as f:
                        oauth_keys = json.load(f)
                    
                    # Use custom OAuth flow that handles both web and installed apps
                    print("🔐 Starting custom OAuth flow...")
                    creds = self._custom_oauth_flow(oauth_keys)
                
                # Save credentials
                with open(CREDENTIALS_FILE, 'w') as f:
                    f.write(creds.to_json())
                print("✅ Credentials saved successfully!")
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise GmailAuthenticationError(f"Authentication failed: {e}")
    
    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """Send an email with optional attachments and CC/BCC."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Validate email addresses
            to_emails = [to] if isinstance(to, str) else to
            for email in to_emails:
                validate_email(email)
            
            # Create message
            message = MIMEMultipart()
            message['to'] = ', '.join(to_emails)
            message['subject'] = subject
            
            if cc:
                cc_emails = [cc] if isinstance(cc, str) else cc
                for email in cc_emails:
                    validate_email(email)
                message['cc'] = ', '.join(cc_emails)
            
            if bcc:
                bcc_emails = [bcc] if isinstance(bcc, str) else bcc
                for email in bcc_emails:
                    validate_email(email)
                message['bcc'] = ', '.join(bcc_emails)
            
            # Add body
            if html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"Attachment file not found: {file_path}")
                    
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    message.attach(part)
            
            # Send message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw_message}
            
            result = self.service.users().messages().send(
                userId='me', body=send_message
            ).execute()
            
            return {
                'success': True,
                'message_id': result['id'],
                'message': f'Email sent successfully to {", ".join(to_emails)}'
            }
            
        except EmailNotValidError as e:
            raise GmailAPIError(f"Invalid email address: {e}")
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to send email: {e}")
    
    async def draft_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """Create an email draft."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Validate email addresses
            to_emails = [to] if isinstance(to, str) else to
            for email in to_emails:
                validate_email(email)
            
            # Create message (same as send_email)
            message = MIMEMultipart()
            message['to'] = ', '.join(to_emails)
            message['subject'] = subject
            
            if cc:
                cc_emails = [cc] if isinstance(cc, str) else cc
                for email in cc_emails:
                    validate_email(email)
                message['cc'] = ', '.join(cc_emails)
            
            if bcc:
                bcc_emails = [bcc] if isinstance(bcc, str) else bcc
                for email in bcc_emails:
                    validate_email(email)
                message['bcc'] = ', '.join(bcc_emails)
            
            # Add body
            if html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"Attachment file not found: {file_path}")
                    
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    message.attach(part)
            
            # Create draft
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            draft_message = {'message': {'raw': raw_message}}
            
            result = self.service.users().drafts().create(
                userId='me', body=draft_message
            ).execute()
            
            return {
                'success': True,
                'draft_id': result['id'],
                'message': f'Draft created successfully for {", ".join(to_emails)}'
            }
            
        except EmailNotValidError as e:
            raise GmailAPIError(f"Invalid email address: {e}")
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to create draft: {e}")
    
    async def read_email(self, message_id: str) -> Dict[str, Any]:
        """Read an email with enhanced attachment information."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Get message
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            # Extract headers
            headers = {}
            for header in message['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']
            
            # Extract body and attachments
            body = self._extract_body(message['payload'])
            attachments = self._extract_attachments(message['payload'])
            
            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': headers.get('subject', ''),
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'cc': headers.get('cc', ''),
                'bcc': headers.get('bcc', ''),
                'date': headers.get('date', ''),
                'body': body,
                'attachments': attachments,
                'labels': message.get('labelIds', []),
                'snippet': message.get('snippet', '')
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to read email: {e}")
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract body from email payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'parts' in part:
                    body = self._extract_body(part)
                    if body:
                        break
        else:
            if payload['mimeType'] in ['text/plain', 'text/html']:
                if 'data' in payload['body']:
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return body
    
    def _extract_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachment information from email payload."""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    attachment = {
                        'filename': part['filename'],
                        'mime_type': part['mimeType'],
                        'size': part['body'].get('size', 0),
                        'attachment_id': part['body'].get('attachmentId', '')
                    }
                    attachments.append(attachment)
                elif 'parts' in part:
                    attachments.extend(self._extract_attachments(part))
        
        return attachments
    
    async def search_emails(
        self,
        query: str,
        max_results: int = 10,
        include_spam_trash: bool = False
    ) -> List[Dict[str, Any]]:
        """Search emails using Gmail query syntax."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Search messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                includeSpamTrash=include_spam_trash
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get detailed info for each message
            detailed_messages = []
            for message in messages:
                try:
                    msg_detail = await self.read_email(message['id'])
                    detailed_messages.append(msg_detail)
                except Exception as e:
                    logger.warning(f"Failed to get details for message {message['id']}: {e}")
            
            return detailed_messages
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to search emails: {e}")
    
    async def modify_email(
        self,
        message_id: str,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add or remove labels from an email."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Convert label names to IDs
            if add_labels:
                add_label_ids = []
                for label in add_labels:
                    label_id = await self._get_label_id(label)
                    if label_id:
                        add_label_ids.append(label_id)
                add_labels = add_label_ids
            
            if remove_labels:
                remove_label_ids = []
                for label in remove_labels:
                    label_id = await self._get_label_id(label)
                    if label_id:
                        remove_label_ids.append(label_id)
                remove_labels = remove_label_ids
            
            # Modify message
            body = {
                'addLabelIds': add_labels or [],
                'removeLabelIds': remove_labels or []
            }
            
            result = self.service.users().messages().modify(
                userId='me', id=message_id, body=body
            ).execute()
            
            return {
                'success': True,
                'message_id': result['id'],
                'labels': result.get('labelIds', [])
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to modify email: {e}")
    
    async def delete_email(self, message_id: str) -> Dict[str, Any]:
        """Permanently delete an email."""
        if not self.service:
            await self.authenticate()
        
        try:
            self.service.users().messages().delete(
                userId='me', id=message_id
            ).execute()
            
            return {
                'success': True,
                'message': f'Email {message_id} deleted successfully'
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to delete email: {e}")
    
    async def batch_modify_emails(
        self,
        message_ids: List[str],
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """Modify labels for multiple emails in batches."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Convert label names to IDs
            if add_labels:
                add_label_ids = []
                for label in add_labels:
                    label_id = await self._get_label_id(label)
                    if label_id:
                        add_label_ids.append(label_id)
                add_labels = add_label_ids
            
            if remove_labels:
                remove_label_ids = []
                for label in remove_labels:
                    label_id = await self._get_label_id(label)
                    if label_id:
                        remove_label_ids.append(label_id)
                remove_labels = remove_label_ids
            
            # Process in batches
            processed = 0
            errors = []
            
            for i in range(0, len(message_ids), batch_size):
                batch = message_ids[i:i + batch_size]
                
                # Batch modify
                body = {
                    'ids': batch,
                    'addLabelIds': add_labels or [],
                    'removeLabelIds': remove_labels or []
                }
                
                try:
                    self.service.users().messages().batchModify(
                        userId='me', body=body
                    ).execute()
                    processed += len(batch)
                except HttpError as e:
                    errors.append(f"Batch {i//batch_size + 1}: {e}")
                    # Try individual modifications for failed batch
                    for msg_id in batch:
                        try:
                            await self.modify_email(msg_id, add_labels, remove_labels)
                            processed += 1
                        except Exception as individual_error:
                            errors.append(f"Message {msg_id}: {individual_error}")
            
            return {
                'success': True,
                'processed': processed,
                'total': len(message_ids),
                'errors': errors
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to batch modify emails: {e}")
    
    async def batch_delete_emails(
        self,
        message_ids: List[str],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """Delete multiple emails in batches."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Process in batches
            processed = 0
            errors = []
            
            for i in range(0, len(message_ids), batch_size):
                batch = message_ids[i:i + batch_size]
                
                # Try batch delete
                body = {'ids': batch}
                
                try:
                    self.service.users().messages().batchDelete(
                        userId='me', body=body
                    ).execute()
                    processed += len(batch)
                except HttpError as e:
                    errors.append(f"Batch {i//batch_size + 1}: {e}")
                    # Try individual deletions for failed batch
                    for msg_id in batch:
                        try:
                            await self.delete_email(msg_id)
                            processed += 1
                        except Exception as individual_error:
                            errors.append(f"Message {msg_id}: {individual_error}")
            
            return {
                'success': True,
                'processed': processed,
                'total': len(message_ids),
                'errors': errors
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to batch delete emails: {e}")
    
    async def list_email_labels(self) -> List[Dict[str, Any]]:
        """List all Gmail labels."""
        if not self.service:
            await self.authenticate()
        
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Format labels
            formatted_labels = []
            for label in labels:
                formatted_labels.append({
                    'id': label['id'],
                    'name': label['name'],
                    'type': label['type'],
                    'message_list_visibility': label.get('messageListVisibility', 'show'),
                    'label_list_visibility': label.get('labelListVisibility', 'labelShow')
                })
            
            return formatted_labels
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to list labels: {e}")
    
    async def create_label(
        self,
        name: str,
        message_list_visibility: str = 'show',
        label_list_visibility: str = 'labelShow'
    ) -> Dict[str, Any]:
        """Create a new Gmail label."""
        if not self.service:
            await self.authenticate()
        
        try:
            label_object = {
                'name': name,
                'messageListVisibility': message_list_visibility,
                'labelListVisibility': label_list_visibility
            }
            
            result = self.service.users().labels().create(
                userId='me', body=label_object
            ).execute()
            
            return {
                'success': True,
                'label_id': result['id'],
                'name': result['name']
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to create label: {e}")
    
    async def update_label(
        self,
        label_id: str,
        name: Optional[str] = None,
        message_list_visibility: Optional[str] = None,
        label_list_visibility: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing Gmail label."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Get current label
            current_label = self.service.users().labels().get(
                userId='me', id=label_id
            ).execute()
            
            # Update fields
            label_object = {
                'name': name or current_label['name'],
                'messageListVisibility': message_list_visibility or current_label.get('messageListVisibility', 'show'),
                'labelListVisibility': label_list_visibility or current_label.get('labelListVisibility', 'labelShow')
            }
            
            result = self.service.users().labels().update(
                userId='me', id=label_id, body=label_object
            ).execute()
            
            return {
                'success': True,
                'label_id': result['id'],
                'name': result['name']
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to update label: {e}")
    
    async def delete_label(self, label_id: str) -> Dict[str, Any]:
        """Delete a Gmail label (only user-created labels)."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Check if it's a system label
            label = self.service.users().labels().get(
                userId='me', id=label_id
            ).execute()
            
            if label['type'] == 'system':
                raise GmailAPIError("Cannot delete system labels")
            
            self.service.users().labels().delete(
                userId='me', id=label_id
            ).execute()
            
            return {
                'success': True,
                'message': f'Label {label["name"]} deleted successfully'
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to delete label: {e}")
    
    async def get_or_create_label(self, name: str) -> str:
        """Get existing label ID or create new label."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Get all labels
            labels = await self.list_email_labels()
            
            # Find existing label (case-insensitive)
            for label in labels:
                if label['name'].lower() == name.lower():
                    return label['id']
            
            # Create new label
            result = await self.create_label(name)
            return result['label_id']
            
        except Exception as e:
            raise GmailAPIError(f"Failed to get or create label: {e}")
    
    async def download_attachment(
        self,
        message_id: str,
        attachment_id: str,
        download_path: str
    ) -> Dict[str, Any]:
        """Download an email attachment."""
        if not self.service:
            await self.authenticate()
        
        try:
            # Get attachment
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id
            ).execute()
            
            # Decode and save
            file_data = base64.urlsafe_b64decode(attachment['data'])
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            with open(download_path, 'wb') as f:
                f.write(file_data)
            
            return {
                'success': True,
                'download_path': download_path,
                'size': len(file_data)
            }
            
        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to download attachment: {e}")
    
    async def _get_label_id(self, label_name: str) -> Optional[str]:
        """Get label ID by name."""
        try:
            labels = await self.list_email_labels()
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    return label['id']
            return None
        except Exception:
            return None


# Global instance
gmail_tools = GmailTools()


# Function tool decorators for agent integration
@function_tool
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    html: bool = False
) -> str:
    """Send an email with optional attachments, CC, BCC, and HTML formatting"""
    try:
        result = await gmail_tools.send_email(
            to=to.split(',') if ',' in to else to,
            subject=subject,
            body=body,
            cc=cc.split(',') if cc and ',' in cc else cc,
            bcc=bcc.split(',') if bcc and ',' in bcc else bcc,
            attachments=attachments,
            html=html
        )
        return f"✅ Email sent successfully! Message ID: {result.get('message_id', 'N/A')}"
    except Exception as e:
        return f"❌ Failed to send email: {e}"


@function_tool
async def draft_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    html: bool = False
) -> str:
    """Create an email draft with optional attachments, CC, BCC, and HTML formatting"""
    try:
        result = await gmail_tools.draft_email(
            to=to.split(',') if ',' in to else to,
            subject=subject,
            body=body,
            cc=cc.split(',') if cc and ',' in cc else cc,
            bcc=bcc.split(',') if bcc and ',' in bcc else bcc,
            attachments=attachments,
            html=html
        )
        return f"✅ Draft created successfully! Draft ID: {result.get('draft_id', 'N/A')}"
    except Exception as e:
        return f"❌ Failed to create draft: {e}"


@function_tool
async def read_email(message_id: str) -> str:
    """Read an email with full details including attachments"""
    try:
        email = await gmail_tools.read_email(message_id)
        
        result = f"""📧 Email Details:
From: {email['from']}
To: {email['to']}
Subject: {email['subject']}
Date: {email['date']}

Body:
{email['body'][:500]}{'...' if len(email['body']) > 500 else ''}
"""
        
        if email['attachments']:
            result += f"\n📎 Attachments ({len(email['attachments'])}):\n"
            for att in email['attachments']:
                result += f"  - {att['filename']} ({att['size']} bytes)\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to read email: {e}"


@function_tool
async def search_emails(query: str, max_results: int = 10) -> str:
    """Search emails using Gmail query syntax (e.g., 'from:user@domain.com', 'is:unread')"""
    try:
        emails = await gmail_tools.search_emails(query, max_results)
        
        if not emails:
            return f"📭 No emails found for query: {query}"
        
        result = f"📧 Found {len(emails)} emails for '{query}':\n\n"
        
        for i, email in enumerate(emails, 1):
            result += f"{i}. From: {email['from']}\n"
            result += f"   Subject: {email['subject']}\n"
            result += f"   Date: {email['date']}\n"
            result += f"   ID: {email['id']}\n"
            result += f"   Snippet: {email['snippet'][:100]}...\n\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to search emails: {e}"


@function_tool
async def modify_email(message_id: str, add_labels: Optional[List[str]] = None, remove_labels: Optional[List[str]] = None) -> str:
    """Add or remove labels from an email (e.g., mark as read/unread, archive, etc.)"""
    try:
        result = await gmail_tools.modify_email(message_id, add_labels, remove_labels)
        return f"✅ Email labels modified successfully! Current labels: {result.get('labels', [])}"
    except Exception as e:
        return f"❌ Failed to modify email: {e}"


@function_tool
async def delete_email(message_id: str) -> str:
    """Permanently delete an email"""
    try:
        result = await gmail_tools.delete_email(message_id)
        return f"✅ Email deleted successfully!"
    except Exception as e:
        return f"❌ Failed to delete email: {e}"


@function_tool
async def list_email_labels() -> str:
    """List all Gmail labels (system and user-defined)"""
    try:
        labels = await gmail_tools.list_email_labels()
        
        system_labels = [l for l in labels if l['type'] == 'system']
        user_labels = [l for l in labels if l['type'] == 'user']
        
        result = f"📋 Gmail Labels ({len(labels)} total):\n\n"
        
        if system_labels:
            result += f"🔧 System Labels ({len(system_labels)}):\n"
            for label in system_labels:
                result += f"  - {label['name']} (ID: {label['id']})\n"
            result += "\n"
        
        if user_labels:
            result += f"👤 User Labels ({len(user_labels)}):\n"
            for label in user_labels:
                result += f"  - {label['name']} (ID: {label['id']})\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to list labels: {e}"


@function_tool
async def create_label(name: str, message_list_visibility: str = 'show', label_list_visibility: str = 'labelShow') -> str:
    """Create a new Gmail label"""
    try:
        result = await gmail_tools.create_label(name, message_list_visibility, label_list_visibility)
        return f"✅ Label '{name}' created successfully! ID: {result.get('label_id', 'N/A')}"
    except Exception as e:
        return f"❌ Failed to create label: {e}"


@function_tool
async def get_latest_emails(count: int = 5) -> str:
    """Get the latest emails from inbox with basic info (subject, sender, snippet)"""
    try:
        emails = await gmail_tools.search_emails('in:inbox', max_results=count)
        
        if not emails:
            return "📭 No emails found in inbox"
        
        result = f"📧 Latest {len(emails)} emails from inbox:\n\n"
        
        for i, email in enumerate(emails, 1):
            result += f"{i}. From: {email['from']}\n"
            result += f"   Subject: {email['subject']}\n"
            result += f"   Date: {email['date']}\n"
            result += f"   ID: {email['id']}\n"
            result += f"   Snippet: {email['snippet'][:100]}...\n\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to get latest emails: {e}"


@function_tool
async def get_latest_email_with_body() -> str:
    """Get the most recent email from inbox with full body content"""
    try:
        emails = await gmail_tools.search_emails('in:inbox', max_results=1)
        
        if not emails:
            return "📭 No emails found in inbox"
        
        latest_email = emails[0]
        
        # Get full email details including body
        full_email = await gmail_tools.read_email(latest_email['id'])
        
        result = f"""📧 Latest Email:

From: {full_email['from']}
To: {full_email['to']}
Subject: {full_email['subject']}
Date: {full_email['date']}

📄 Full Body:
{full_email['body']}
"""
        
        if full_email['attachments']:
            result += f"\n📎 Attachments ({len(full_email['attachments'])}):\n"
            for att in full_email['attachments']:
                result += f"  - {att['filename']} ({att['size']} bytes)\n"
        
        return result
    except Exception as e:
        return f"❌ Failed to get latest email with body: {e}"