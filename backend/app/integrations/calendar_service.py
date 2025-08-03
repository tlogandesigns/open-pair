from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from app.models.database_models import Agent, OpenHouse, AgentAvailability

class CalendarService:
    """Google Calendar integration for agent availability and scheduling"""
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 
                       'https://www.googleapis.com/auth/calendar.events']
        self.credentials_file = "app/integrations/credentials.json"
        self.token_file = "app/integrations/token.json"
        self.service = None
    
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    return False
            else:
                if not os.path.exists(self.credentials_file):
                    print("Google credentials file not found. Calendar integration disabled.")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error in OAuth flow: {e}")
                    return False
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Error building calendar service: {e}")
            return False
    
    def check_agent_availability(self, agent: Agent, start_time: datetime, 
                               end_time: datetime) -> Dict[str, Any]:
        """Check if agent is available for the given time slot"""
        if not self.service:
            # Fallback to database availability if calendar not available
            return self.check_database_availability(agent, start_time, end_time)
        
        try:
            # Get agent's primary calendar events
            events_result = self.service.events().list(
                calendarId='primary',  # In production, use agent-specific calendar
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Check for conflicts
            conflicts = []
            for event in events:
                event_start = datetime.fromisoformat(
                    event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00')
                )
                event_end = datetime.fromisoformat(
                    event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00')
                )
                
                # Check for overlap
                if not (end_time <= event_start or start_time >= event_end):
                    conflicts.append({
                        'title': event.get('summary', 'Busy'),
                        'start': event_start,
                        'end': event_end
                    })
            
            is_available = len(conflicts) == 0
            
            return {
                'available': is_available,
                'conflicts': conflicts,
                'source': 'google_calendar'
            }
            
        except HttpError as error:
            print(f"Error checking calendar availability: {error}")
            # Fallback to database availability
            return self.check_database_availability(agent, start_time, end_time)
    
    def check_database_availability(self, agent: Agent, start_time: datetime, 
                                  end_time: datetime) -> Dict[str, Any]:
        """Fallback availability check using database-stored availability"""
        day_of_week = start_time.weekday()  # 0=Monday, 6=Sunday
        start_time_str = start_time.strftime("%H:%M")
        end_time_str = end_time.strftime("%H:%M")
        
        # Check if agent has availability set for this day
        from app.database.connection import SessionLocal
        db = SessionLocal()
        
        try:
            availability = db.query(AgentAvailability).filter(
                AgentAvailability.agent_id == agent.id,
                AgentAvailability.day_of_week == day_of_week,
                AgentAvailability.is_available == True
            ).first()
            
            if not availability:
                return {
                    'available': False,
                    'reason': 'No availability set for this day',
                    'source': 'database'
                }
            
            # Check time overlap
            if (availability.start_time <= start_time_str and 
                availability.end_time >= end_time_str):
                return {
                    'available': True,
                    'source': 'database'
                }
            else:
                return {
                    'available': False,
                    'reason': f'Outside available hours ({availability.start_time}-{availability.end_time})',
                    'source': 'database'
                }
        
        finally:
            db.close()
    
    def create_calendar_invite(self, open_house: OpenHouse, agent: Agent, 
                             listing_address: str) -> Dict[str, Any]:
        """Create calendar invite for the selected agent"""
        if not self.service:
            return {'success': False, 'error': 'Calendar service not available'}
        
        event = {
            'summary': f'Open House: {listing_address}',
            'description': f'Host open house at {listing_address}\n'
                          f'Open House ID: {open_house.id}\n'
                          f'Host: {agent.name}\n'
                          f'Contact: {agent.email}',
            'start': {
                'dateTime': open_house.start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',  # Configure based on property location
            },
            'end': {
                'dateTime': open_house.end_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'attendees': [
                {'email': agent.email}
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},       # 1 hour before
                ],
            },
        }
        
        try:
            created_event = self.service.events().insert(
                calendarId='primary',  # In production, use appropriate calendar
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'created_at': datetime.now()
            }
            
        except HttpError as error:
            return {
                'success': False,
                'error': str(error)
            }
    
    def update_calendar_invite(self, event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing calendar invite"""
        if not self.service:
            return {'success': False, 'error': 'Calendar service not available'}
        
        try:
            # First get the current event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Apply updates
            event.update(updates)
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': updated_event['id'],
                'updated_at': datetime.now()
            }
            
        except HttpError as error:
            return {
                'success': False,
                'error': str(error)
            }
    
    def cancel_calendar_invite(self, event_id: str) -> Dict[str, Any]:
        """Cancel/delete calendar invite"""
        if not self.service:
            return {'success': False, 'error': 'Calendar service not available'}
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return {
                'success': True,
                'cancelled_at': datetime.now()
            }
            
        except HttpError as error:
            return {
                'success': False,
                'error': str(error)
            }
    
    def get_agent_busy_times(self, agent: Agent, start_date: datetime, 
                           end_date: datetime) -> List[Dict[str, Any]]:
        """Get all busy times for an agent in a date range"""
        if not self.service:
            return []
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            busy_times = []
            
            for event in events:
                if event.get('transparency') == 'transparent':
                    continue  # Skip free/available events
                
                start_time = datetime.fromisoformat(
                    event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00')
                )
                end_time = datetime.fromisoformat(
                    event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00')
                )
                
                busy_times.append({
                    'title': event.get('summary', 'Busy'),
                    'start': start_time,
                    'end': end_time,
                    'all_day': 'date' in event['start']
                })
            
            return busy_times
            
        except HttpError as error:
            print(f"Error getting busy times: {error}")
            return []

# Global instance
calendar_service = CalendarService()
