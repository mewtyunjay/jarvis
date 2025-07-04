import os
import json
import re
import webbrowser
import urllib.parse
import secrets
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path
import asyncio
import logging
from zoneinfo import ZoneInfo
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from agents import function_tool
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Configuration paths - matching MCP server exactly
CONFIG_DIR = os.path.expanduser("~/.config/google-calendar-mcp")
TOKENS_FILE = os.path.join(CONFIG_DIR, "tokens.json")
LEGACY_TOKENS_FILE = os.path.expanduser("~/.gcp-saved-tokens.json")

# OAuth credentials path - matching MCP server priority
OAUTH_CREDENTIALS_PATH = os.getenv("GOOGLE_OAUTH_CREDENTIALS") or os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "gcp-oauth.keys.json"
)

# Account mode detection - matching MCP server exactly
ACCOUNT_MODE = os.getenv("GOOGLE_ACCOUNT_MODE") or ("test" if os.getenv("NODE_ENV") == "test" else "normal")

# ISO 8601 datetime regex - matching MCP server exactly
ISO_8601_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?$')

class CalendarAuthenticationError(Exception):
    """Raised when Calendar authentication fails."""
    pass

class CalendarAPIError(Exception):
    """Raised when Calendar API operations fail."""
    pass

class InvalidRequestError(Exception):
    """Raised when request parameters are invalid."""
    pass

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler for OAuth callback - matching MCP server implementation"""

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
            html_content = '''
                <html>
                <head>
                    <title>Google Calendar Authentication</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                        .success { color: #4CAF50; }
                        .container { max-width: 600px; margin: 0 auto; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="success">✓ Authentication Successful!</h1>
                        <p>Your Google Calendar has been successfully connected.</p>
                        <p>You can now close this window and return to the application.</p>
                        <script>
                            setTimeout(() => window.close(), 3000);
                        </script>
                    </div>
                </body>
                </html>
            '''
            self.wfile.write(html_content.encode('utf-8'))
        elif 'error' in query_params:
            self.auth_code_container['error'] = query_params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_message = query_params['error'][0]
            error_html = f'''
                <html>
                <head>
                    <title>Authentication Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
                        .error {{ color: #f44336; }}
                        .container {{ max-width: 600px; margin: 0 auto; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">✗ Authentication Error</h1>
                        <p>Error: {error_message}</p>
                        <p>Please close this window and try again.</p>
                    </div>
                </body>
                </html>
            '''
            self.wfile.write(error_html.encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            invalid_html = '''
                <html>
                <head>
                    <title>Invalid Callback</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                        .error { color: #f44336; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">✗ Invalid Callback</h1>
                        <p>No authorization code received.</p>
                    </div>
                </body>
                </html>
            '''
            self.wfile.write(invalid_html.encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

def find_available_port(start_port=3500, max_attempts=6):
    """Find an available port starting from start_port - matching MCP server ports 3500-3505"""
    for i in range(max_attempts):
        port = start_port + i
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise CalendarAuthenticationError(f"No available ports found in range {start_port}-{start_port + max_attempts - 1}")

class CalendarTools:
    """Google Calendar Tools class providing all calendar functionality."""

    def __init__(self):
        self.service = None
        self._ensure_config_dir()
        self._migrate_legacy_tokens()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists - matching MCP server structure"""
        os.makedirs(CONFIG_DIR, exist_ok=True)

        # Set proper permissions for config directory
        try:
            os.chmod(CONFIG_DIR, 0o700)
        except OSError:
            pass

    def _migrate_legacy_tokens(self):
        """Migrate legacy tokens if they exist - matching MCP server migration logic"""
        if os.path.exists(LEGACY_TOKENS_FILE) and not os.path.exists(TOKENS_FILE):
            try:
                with open(LEGACY_TOKENS_FILE, 'r') as f:
                    legacy_tokens = json.load(f)

                # Convert to new multi-account format
                new_tokens = {
                    "normal": legacy_tokens
                }

                with open(TOKENS_FILE, 'w') as f:
                    json.dump(new_tokens, f, indent=2)

                # Set secure permissions
                os.chmod(TOKENS_FILE, 0o600)

                # Clean up legacy file
                os.remove(LEGACY_TOKENS_FILE)
                logger.info("Migrated legacy token file to new format")

            except Exception as e:
                logger.warning(f"Failed to migrate legacy tokens: {e}")

    def _load_oauth_credentials(self):
        """Load OAuth credentials with priority matching MCP server"""
        # Priority 1: Environment variable
        if os.getenv("GOOGLE_OAUTH_CREDENTIALS"):
            try:
                return json.loads(os.getenv("GOOGLE_OAUTH_CREDENTIALS"))
            except json.JSONDecodeError as e:
                raise CalendarAuthenticationError(f"Invalid JSON in GOOGLE_OAUTH_CREDENTIALS: {e}")

        # Priority 2: File path
        if not os.path.exists(OAUTH_CREDENTIALS_PATH):
            raise CalendarAuthenticationError(f"OAuth credentials file not found at {OAUTH_CREDENTIALS_PATH}")

        try:
            with open(OAUTH_CREDENTIALS_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise CalendarAuthenticationError(f"Invalid JSON in OAuth credentials file: {e}")

    def _custom_oauth_flow(self, oauth_keys):
        """Custom OAuth flow supporting multiple credential formats - matching MCP server exactly"""
        # Extract client configuration - supporting both formats
        if 'installed' in oauth_keys:
            client_config = oauth_keys['installed']
        elif 'client_id' in oauth_keys:
            client_config = oauth_keys
        else:
            raise CalendarAuthenticationError("Invalid OAuth credentials format. Expected 'installed' object or direct client_id/client_secret")

        client_id = client_config.get('client_id')
        client_secret = client_config.get('client_secret')
        redirect_uris = client_config.get('redirect_uris', ['http://localhost:3000/oauth2callback'])

        if not client_id or not client_secret:
            raise CalendarAuthenticationError("Missing client_id or client_secret in OAuth credentials")

        # Handle redirect URI from credentials
        if redirect_uris and isinstance(redirect_uris, list) and redirect_uris[0]:
            base_redirect = redirect_uris[0]
            # If it's just "http://localhost", add port and path
            if base_redirect == "http://localhost":
                port = find_available_port()
                redirect_uri = f"http://localhost:{port}/oauth2callback"
            else:
                redirect_uri = base_redirect
                # Extract port if specified
                if 'localhost:' in redirect_uri:
                    try:
                        port = int(redirect_uri.split(':')[2].split('/')[0])
                    except (IndexError, ValueError):
                        port = find_available_port()
                else:
                    port = find_available_port()
        else:
            # Default fallback
            port = find_available_port()
            redirect_uri = f"http://localhost:{port}/oauth2callback"

        # Create authorization URL
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={urllib.parse.quote(client_id)}&"
            f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
            f"scope={urllib.parse.quote(' '.join(SCOPES))}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent"
        )

        # Container for authorization code
        auth_code_container = {}

        # Create HTTP server for callback
        def handler_factory(container):
            def create_handler(*args, **kwargs):
                return OAuthCallbackHandler(container, *args, **kwargs)
            return create_handler

        try:
            httpd = HTTPServer(('localhost', port), handler_factory(auth_code_container))
            httpd.timeout = 120  # 2 minutes timeout

            print(f"🔗 Please visit this URL to authenticate Google Calendar:")
            print(f"   {auth_url}")
            print(f"💡 Opening browser automatically...")

            # Open browser
            try:
                webbrowser.open(auth_url)
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
                print("   Please copy and paste the URL above into your browser")

            # Wait for callback
            print("⏳ Waiting for authentication callback...")
            httpd.handle_request()

        except Exception as e:
            raise CalendarAuthenticationError(f"Failed to start OAuth callback server: {e}")

        # Check for authorization code
        if 'error' in auth_code_container:
            raise CalendarAuthenticationError(f"OAuth error: {auth_code_container['error']}")

        if 'code' not in auth_code_container:
            raise CalendarAuthenticationError("No authorization code received")

        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': auth_code_container['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }

        try:
            response = requests.post(token_url, data=token_data, timeout=30)
            response.raise_for_status()
            token_info = response.json()

            # Create credentials object
            credentials = Credentials(
                token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                token_uri=token_url,
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )

            return credentials

        except requests.RequestException as e:
            raise CalendarAuthenticationError(f"Failed to exchange authorization code for tokens: {e}")

    def _load_tokens(self):
        """Load tokens from file with multi-account support"""
        if not os.path.exists(TOKENS_FILE):
            return None

        try:
            with open(TOKENS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load tokens: {e}")
            return None

    def _save_tokens(self, credentials: Credentials):
        """Save tokens to file with multi-account support"""
        tokens = self._load_tokens() or {}

        # Convert credentials to dict
        token_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes) if credentials.scopes else SCOPES
        }

        # Store under account mode
        tokens[ACCOUNT_MODE] = token_dict

        # Write tokens file
        try:
            with open(TOKENS_FILE, 'w') as f:
                json.dump(tokens, f, indent=2)

            # Set secure permissions
            os.chmod(TOKENS_FILE, 0o600)

        except IOError as e:
            raise CalendarAuthenticationError(f"Failed to save tokens: {e}")

    def _credentials_from_tokens(self, token_dict):
        """Create credentials object from token dict"""
        return Credentials(
            token=token_dict.get('token'),
            refresh_token=token_dict.get('refresh_token'),
            token_uri=token_dict.get('token_uri'),
            client_id=token_dict.get('client_id'),
            client_secret=token_dict.get('client_secret'),
            scopes=token_dict.get('scopes', SCOPES)
        )

    def _is_token_expired(self, credentials: Credentials) -> bool:
        """Check if token is expired with 5-minute buffer - matching MCP server"""
        if not credentials.expiry:
            return False

        # 5-minute buffer for expiry
        buffer = timedelta(minutes=5)
        return datetime.now(timezone.utc) >= (credentials.expiry - buffer)

    async def authenticate(self):
        """Authenticate with Google Calendar API - matching MCP server flow exactly"""
        # Load existing tokens
        tokens = self._load_tokens()
        credentials = None

        if tokens and ACCOUNT_MODE in tokens:
            try:
                credentials = self._credentials_from_tokens(tokens[ACCOUNT_MODE])

                # Check if token needs refresh
                if self._is_token_expired(credentials):
                    logger.info("Token expired, refreshing...")
                    credentials.refresh(Request())
                    self._save_tokens(credentials)

            except Exception as e:
                logger.warning(f"Failed to load/refresh existing tokens: {e}")
                credentials = None

        # If no valid credentials, perform OAuth flow
        if not credentials:
            oauth_keys = self._load_oauth_credentials()
            credentials = self._custom_oauth_flow(oauth_keys)
            self._save_tokens(credentials)

        # Create Calendar service
        try:
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info(f"Successfully authenticated Google Calendar for account mode: {ACCOUNT_MODE}")

        except Exception as e:
            raise CalendarAuthenticationError(f"Failed to create Calendar service: {e}")

    def _validate_iso_datetime(self, dt_string: str) -> bool:
        """Validate ISO 8601 datetime format - matching MCP server regex exactly"""
        return bool(ISO_8601_REGEX.match(dt_string))

    def _validate_timezone(self, tz_string: str) -> bool:
        """Validate IANA timezone format"""
        try:
            ZoneInfo(tz_string)
            return True
        except Exception:
            return False

    def _format_datetime_for_api(self, dt_string: str, timezone: Optional[str] = None):
        """Format datetime for Google Calendar API - matching MCP server logic exactly"""
        # If datetime string contains timezone info, use it as-is
        if dt_string.endswith('Z') or '+' in dt_string[-6:] or dt_string.count('-') > 2:
            return {'dateTime': dt_string}

        # If timezone provided, add it
        if timezone:
            return {'dateTime': dt_string, 'timeZone': timezone}

        # Default to UTC if no timezone info
        return {'dateTime': dt_string + 'Z'}

    def _handle_api_error(self, error: HttpError) -> str:
        """Handle Google Calendar API errors - matching MCP server error mapping"""
        error_code = error.resp.status
        error_message = str(error)

        if error_code == 403:
            return f"Access denied: {error_message}"
        elif error_code == 404:
            return f"Resource not found: {error_message}"
        elif error_code == 429:
            return f"Rate limit exceeded: {error_message}"
        elif error_code >= 500:
            return f"Server error: {error_message}"
        else:
            return f"API error: {error_message}"

# Global instance
calendar_tools = CalendarTools()

# Simplified tool implementations with @function_tool decorators

@function_tool
async def list_calendars() -> str:
    """List all available calendars"""
    try:
        calendar_list = calendar_tools.service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])

        if not calendars:
            return "📅 No calendars found"

        result = f"📅 Found {len(calendars)} calendar(s):\n\n"
        for calendar in calendars:
            result += f"📋 **{calendar.get('summary', 'Unnamed Calendar')}**\n"
            result += f"   ID: `{calendar['id']}`\n"
            result += f"   Access: {calendar.get('accessRole', 'Unknown')}\n"
            result += f"   Primary: {'Yes' if calendar.get('primary', False) else 'No'}\n"
            if calendar.get('description'):
                result += f"   Description: {calendar['description']}\n"
            result += "\n"

        return result

    except HttpError as e:
        error_msg = calendar_tools._handle_api_error(e)
        return f"❌ Failed to list calendars: {error_msg}"
    except Exception as e:
        return f"❌ Error listing calendars: {str(e)}"

@function_tool
async def list_events(calendar_id: str, time_min: Optional[str] = None,
                     time_max: Optional[str] = None, time_zone: Optional[str] = None) -> str:
    """List events from a calendar

    Args:
        calendar_id: Calendar ID or JSON string array like '["cal1", "cal2"]'
        time_min: Start time in ISO 8601 format (optional)
        time_max: End time in ISO 8601 format (optional)
        time_zone: IANA timezone (optional)
    """
    try:
        # Validate datetime inputs
        if time_min and not calendar_tools._validate_iso_datetime(time_min):
            return "❌ Invalid time_min format. Use ISO 8601 format (e.g., '2024-01-01T00:00:00')"

        if time_max and not calendar_tools._validate_iso_datetime(time_max):
            return "❌ Invalid time_max format. Use ISO 8601 format (e.g., '2024-01-01T23:59:59')"

        if time_zone and not calendar_tools._validate_timezone(time_zone):
            return f"❌ Invalid timezone: {time_zone}"

        # Parse calendar IDs - support JSON string arrays
        calendar_ids = []
        if calendar_id.strip().startswith('['):
            try:
                calendar_ids = json.loads(calendar_id)
            except json.JSONDecodeError:
                calendar_ids = [calendar_id]
        else:
            calendar_ids = [calendar_id]

        if len(calendar_ids) > 50:
            return "❌ Maximum 50 calendars allowed per request"

        # Build query parameters
        query_params = {
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': 250
        }

        if time_min:
            query_params['timeMin'] = time_min
        if time_max:
            query_params['timeMax'] = time_max
        if time_zone:
            query_params['timeZone'] = time_zone

        # Fetch events from all calendars in parallel
        all_events = []
        errors = []

        async def fetch_calendar_events_safe(cal_id):
            """Safely fetch events from a single calendar using a new service instance"""
            try:
                # Create a new service instance for thread safety
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                
                # Get existing credentials
                tokens = calendar_tools._load_tokens()
                if tokens and ACCOUNT_MODE in tokens:
                    credentials = calendar_tools._credentials_from_tokens(tokens[ACCOUNT_MODE])
                else:
                    raise CalendarAuthenticationError("No valid credentials found")
                
                # Create service in executor for thread safety
                def create_service_and_fetch():
                    service = build('calendar', 'v3', credentials=credentials)
                    return service.events().list(calendarId=cal_id, **query_params).execute()
                
                events_result = await asyncio.get_event_loop().run_in_executor(
                    None, create_service_and_fetch
                )

                events = events_result.get('items', [])
                for event in events:
                    event['calendarId'] = cal_id

                return events, None

            except HttpError as e:
                error_msg = calendar_tools._handle_api_error(e)
                return [], f"Calendar {cal_id}: {error_msg}"
            except Exception as e:
                return [], f"Calendar {cal_id}: {str(e)}"

        # Execute calendar fetches in parallel with separate service instances
        tasks = [fetch_calendar_events_safe(cal_id) for cal_id in calendar_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                errors.append(f"Unexpected error: {str(result)}")
            else:
                events, error = result
                if error:
                    errors.append(error)
                else:
                    all_events.extend(events)

        # Sort all events by start time
        all_events.sort(key=lambda x: x.get('start', {}).get('dateTime', x.get('start', {}).get('date', '')))

        # Format response
        result = f"📅 Found {len(all_events)} event(s)"
        if len(calendar_ids) > 1:
            result += f" across {len(calendar_ids)} calendar(s)"
        result += ":\n\n"

        for event in all_events:
            start = event.get('start', {})

            # Format start time in user's local timezone
            start_time = start.get('dateTime', start.get('date', 'Unknown'))
            if start_time != 'Unknown':
                try:
                    if 'T' in start_time:
                        # Parse UTC time and convert to local timezone
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        local_dt = dt.astimezone()  # Convert to system timezone
                        start_display = local_dt.strftime('%H:%M')  # Just show time, not date
                    else:
                        start_display = "All day"
                except:
                    start_display = start_time
            else:
                start_display = "Unknown"

            result += f"📋 **{event.get('summary', 'Untitled Event')}**\n"
            result += f"   📅 {start_display}\n"
            result += f"   🆔 {event.get('id')}\n"
            result += f"   📚 Calendar: {event.get('calendarId')}\n"

            if event.get('description'):
                desc = event['description'][:100]
                if len(event['description']) > 100:
                    desc += "..."
                result += f"   📝 {desc}\n"

            if event.get('location'):
                result += f"   📍 {event['location']}\n"

            result += "\n"

        if errors:
            result += f"\n⚠️  Some calendars had errors:\n"
            for error in errors:
                result += f"   • {error}\n"

        return result

    except Exception as e:
        return f"❌ Error listing events: {str(e)}"

@function_tool
async def search_events(calendar_id: str, query: str, time_min: str, time_max: str,
                       time_zone: Optional[str] = None) -> str:
    """Search for events by text query

    Args:
        calendar_id: Calendar ID (use 'primary' for main calendar)
        query: Free text search query
        time_min: Start time in ISO 8601 format
        time_max: End time in ISO 8601 format
        time_zone: IANA timezone (optional)
    """
    try:
        # Validate inputs
        if not calendar_tools._validate_iso_datetime(time_min):
            return "❌ Invalid time_min format. Use ISO 8601 format (e.g., '2024-01-01T00:00:00')"

        if not calendar_tools._validate_iso_datetime(time_max):
            return "❌ Invalid time_max format. Use ISO 8601 format (e.g., '2024-01-01T23:59:59')"

        if time_zone and not calendar_tools._validate_timezone(time_zone):
            return f"❌ Invalid timezone: {time_zone}"

        # Build query parameters
        query_params = {
            'q': query,
            'timeMin': time_min,
            'timeMax': time_max,
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': 100
        }

        if time_zone:
            query_params['timeZone'] = time_zone

        # Search events
        events_result = calendar_tools.service.events().list(
            calendarId=calendar_id,
            **query_params
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return f"🔍 No events found matching '{query}'"

        result = f"🔍 Found {len(events)} event(s) matching '{query}':\n\n"

        for event in events:
            start = event.get('start', {})
            start_time = start.get('dateTime', start.get('date', 'Unknown'))

            # Format start time in user's local timezone
            if start_time != 'Unknown':
                try:
                    if 'T' in start_time:
                        # Parse UTC time and convert to local timezone
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        local_dt = dt.astimezone()  # Convert to system timezone
                        start_display = local_dt.strftime('%H:%M')  # Just show time, not date
                    else:
                        start_display = "All day"
                except:
                    start_display = start_time
            else:
                start_display = "Unknown"

            result += f"📋 **{event.get('summary', 'Untitled Event')}**\n"
            result += f"   📅 {start_display}\n"
            result += f"   🆔 {event.get('id')}\n"

            if event.get('description'):
                desc = event['description'][:100]
                if len(event['description']) > 100:
                    desc += "..."
                result += f"   📝 {desc}\n"

            if event.get('location'):
                result += f"   📍 {event['location']}\n"

            result += "\n"

        return result

    except HttpError as e:
        error_msg = calendar_tools._handle_api_error(e)
        return f"❌ Failed to search events: {error_msg}"
    except Exception as e:
        return f"❌ Error searching events: {str(e)}"

@function_tool
async def list_colors() -> str:
    """List available color IDs for calendar events"""
    try:
        colors = calendar_tools.service.colors().get().execute()

        result = "🎨 Available event colors:\n\n"

        event_colors = colors.get('event', {})
        for color_id, color_info in event_colors.items():
            result += f"🎨 **Color {color_id}**\n"
            result += f"   Background: {color_info.get('background', 'Unknown')}\n"
            result += f"   Foreground: {color_info.get('foreground', 'Unknown')}\n\n"

        return result

    except HttpError as e:
        error_msg = calendar_tools._handle_api_error(e)
        return f"❌ Failed to list colors: {error_msg}"
    except Exception as e:
        return f"❌ Error listing colors: {str(e)}"

@function_tool
async def create_event(calendar_id: str, summary: str, start: str, end: str,
                      description: Optional[str] = None, time_zone: Optional[str] = None,
                      location: Optional[str] = None) -> str:
    """Create a new calendar event

    Args:
        calendar_id: Calendar ID to create event in
        summary: Event title
        start: Start time in ISO 8601 format
        end: End time in ISO 8601 format
        description: Event description (optional)
        time_zone: IANA timezone (optional)
        location: Event location (optional)
    """
    try:
        # Validate datetime inputs
        if not calendar_tools._validate_iso_datetime(start):
            return "❌ Invalid start time format. Use ISO 8601 format (e.g., '2024-01-01T10:00:00')"

        if not calendar_tools._validate_iso_datetime(end):
            return "❌ Invalid end time format. Use ISO 8601 format (e.g., '2024-01-01T11:00:00')"

        if time_zone and not calendar_tools._validate_timezone(time_zone):
            return f"❌ Invalid timezone: {time_zone}"

        # Build event object
        event = {
            'summary': summary,
            'start': calendar_tools._format_datetime_for_api(start, time_zone),
            'end': calendar_tools._format_datetime_for_api(end, time_zone),
        }

        if description:
            event['description'] = description

        if location:
            event['location'] = location

        # Create event
        created_event = calendar_tools.service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

        # Format response
        result = f"✅ Event created successfully!\n\n"
        result += f"📋 **{created_event.get('summary')}**\n"
        result += f"🆔 Event ID: {created_event.get('id')}\n"
        result += f"📅 Start: {start}\n"
        result += f"📅 End: {end}\n"

        if created_event.get('htmlLink'):
            result += f"🔗 Link: {created_event['htmlLink']}\n"

        return result

    except HttpError as e:
        error_msg = calendar_tools._handle_api_error(e)
        return f"❌ Failed to create event: {error_msg}"
    except Exception as e:
        return f"❌ Error creating event: {str(e)}"

@function_tool
async def update_event(calendar_id: str, event_id: str, summary: Optional[str] = None,
                      description: Optional[str] = None, start: Optional[str] = None,
                      end: Optional[str] = None, time_zone: Optional[str] = None,
                      location: Optional[str] = None) -> str:
    """Update an existing calendar event

    Args:
        calendar_id: Calendar ID
        event_id: Event ID to update
        summary: Event title (optional)
        description: Event description (optional)
        start: Start time in ISO 8601 format (optional)
        end: End time in ISO 8601 format (optional)
        time_zone: IANA timezone (optional)
        location: Event location (optional)
    """
    try:
        # Validate datetime inputs
        if start and not calendar_tools._validate_iso_datetime(start):
            return "❌ Invalid start time format. Use ISO 8601 format (e.g., '2024-01-01T10:00:00')"

        if end and not calendar_tools._validate_iso_datetime(end):
            return "❌ Invalid end time format. Use ISO 8601 format (e.g., '2024-01-01T11:00:00')"

        if time_zone and not calendar_tools._validate_timezone(time_zone):
            return f"❌ Invalid timezone: {time_zone}"

        # Build update object
        update_data = {}

        if summary is not None:
            update_data['summary'] = summary

        if description is not None:
            update_data['description'] = description

        if start:
            update_data['start'] = calendar_tools._format_datetime_for_api(start, time_zone)

        if end:
            update_data['end'] = calendar_tools._format_datetime_for_api(end, time_zone)

        if location is not None:
            update_data['location'] = location

        # Update event
        updated_event = calendar_tools.service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=update_data
        ).execute()

        # Format response
        result = f"✅ Event updated successfully!\n\n"
        result += f"📋 **{updated_event.get('summary')}**\n"
        result += f"🆔 Event ID: {updated_event.get('id')}\n"

        if updated_event.get('htmlLink'):
            result += f"🔗 Link: {updated_event['htmlLink']}\n"

        return result

    except HttpError as e:
        error_msg = calendar_tools._handle_api_error(e)
        return f"❌ Failed to update event: {error_msg}"
    except Exception as e:
        return f"❌ Error updating event: {str(e)}"

@function_tool
async def delete_event(calendar_id: str, event_id: str) -> str:
    """Delete a calendar event

    Args:
        calendar_id: Calendar ID
        event_id: Event ID to delete
    """
    try:
        # Get event details before deletion
        event = calendar_tools.service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        event_title = event.get('summary', 'Untitled Event')

        # Delete event
        calendar_tools.service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        return f"✅ Event '{event_title}' deleted successfully!"

    except HttpError as e:
        error_msg = calendar_tools._handle_api_error(e)
        return f"❌ Failed to delete event: {error_msg}"
    except Exception as e:
        return f"❌ Error deleting event: {str(e)}"

@function_tool
async def get_freebusy(calendars: str, time_min: str, time_max: str,
                      time_zone: Optional[str] = None) -> str:
    """Query free/busy information for calendars (max 3 months)

    Args:
        calendars: JSON string of calendar objects like '[{"id": "calendar1"}, {"id": "calendar2"}]'
        time_min: Start time in ISO 8601 format
        time_max: End time in ISO 8601 format (max 3 months from time_min)
        time_zone: IANA timezone (optional)
    """
    try:
        # Validate datetime inputs
        if not calendar_tools._validate_iso_datetime(time_min):
            return "❌ Invalid time_min format. Use ISO 8601 format (e.g., '2024-01-01T00:00:00')"

        if not calendar_tools._validate_iso_datetime(time_max):
            return "❌ Invalid time_max format. Use ISO 8601 format (e.g., '2024-01-01T23:59:59')"

        if time_zone and not calendar_tools._validate_timezone(time_zone):
            return f"❌ Invalid timezone: {time_zone}"

        # Parse calendars JSON
        try:
            calendars_list = json.loads(calendars)
            if not isinstance(calendars_list, list):
                return "❌ calendars must be a JSON array of objects with 'id' key"
        except json.JSONDecodeError:
            return "❌ Invalid JSON format for calendars parameter"

        # Validate calendar objects
        for cal in calendars_list:
            if not isinstance(cal, dict) or 'id' not in cal:
                return "❌ Each calendar must be an object with 'id' key"

        # Validate time range (max 3 months)
        try:
            start_dt = datetime.fromisoformat(time_min.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(time_max.replace('Z', '+00:00'))

            if (end_dt - start_dt).days > 90:
                return "❌ Time range cannot exceed 3 months"

        except ValueError:
            return "❌ Invalid datetime format in time_min or time_max"

        # Build request body
        request_body = {
            'timeMin': time_min,
            'timeMax': time_max,
            'items': calendars_list
        }

        if time_zone:
            request_body['timeZone'] = time_zone

        # Query free/busy
        freebusy_result = calendar_tools.service.freebusy().query(
            body=request_body
        ).execute()

        # Format response
        result = f"📅 Free/busy information for {len(calendars_list)} calendar(s):\n\n"

        calendars_data = freebusy_result.get('calendars', {})

        for cal in calendars_list:
            cal_id = cal['id']
            cal_data = calendars_data.get(cal_id, {})

            result += f"📋 **Calendar: {cal_id}**\n"

            # Show errors if any
            if 'errors' in cal_data:
                result += f"   ❌ Errors:\n"
                for error in cal_data['errors']:
                    result += f"      • {error.get('reason', 'Unknown')}: {error.get('domain', 'Unknown')}\n"

            # Show busy periods
            busy_periods = cal_data.get('busy', [])
            if busy_periods:
                result += f"   🔴 Busy periods ({len(busy_periods)}):\n"
                for period in busy_periods:
                    start_time = period.get('start', 'Unknown')
                    end_time = period.get('end', 'Unknown')
                    result += f"      • {start_time} - {end_time}\n"
            else:
                result += f"   ✅ No busy periods found\n"

            result += "\n"

        return result

    except HttpError as e:
        error_msg = calendar_tools._handle_api_error(e)
        return f"❌ Failed to get free/busy information: {error_msg}"
    except Exception as e:
        return f"❌ Error getting free/busy information: {str(e)}"

@function_tool
async def get_current_time(time_zone: Optional[str] = None) -> str:
    """Get current system time and timezone information with auto-detected user timezone

    Args:
        time_zone: IANA timezone (optional, defaults to auto-detected local timezone)
    """
    try:
        now_utc = datetime.now(timezone.utc)
        local_time = now_utc.astimezone()  # Auto-detect system timezone

        # Get user's local timezone string
        user_timezone = str(local_time.tzinfo)

        # Use provided timezone or default to auto-detected
        if time_zone:
            if not calendar_tools._validate_timezone(time_zone):
                return f"❌ Invalid timezone: {time_zone}"
            try:
                tz = ZoneInfo(time_zone)
                display_time = now_utc.astimezone(tz)
                timezone_name = time_zone
            except Exception as e:
                return f"❌ Error converting to timezone {time_zone}: {str(e)}"
        else:
            display_time = local_time
            timezone_name = user_timezone

        # Format today's date for calendar queries
        today_start = display_time.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = display_time.replace(hour=23, minute=59, second=59, microsecond=999999)

        result = f"🕐 Current time information:\n\n"
        result += f"🏠 **Local Time ({timezone_name})**: {display_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        result += f"📅 **Today's Date**: {display_time.strftime('%Y-%m-%d')}\n"
        result += f"⏰ **For Calendar Queries**:\n"
        result += f"   Start of today: {today_start.isoformat()}\n"
        result += f"   End of today: {today_end.isoformat()}\n"
        result += f"   Timezone: {timezone_name}\n"

        return result

    except Exception as e:
        return f"❌ Error getting current time: {str(e)}"
