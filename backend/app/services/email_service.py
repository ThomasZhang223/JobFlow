import resend

from app.core.config import settings
from app.schemas.messages import ScrapeUpdateMessage
from app.services.database_service import get_user_email

resend.api_key = settings.resend_api_key

def send_scrape_complete_email(user_id: str, message: ScrapeUpdateMessage):
    try:
        to_email = get_user_email(user_id)
        params: resend.Emails.SendParams = {
            'from': f'JobFlow <{settings.test_from_email}>',
            'to': [to_email],
            'subject': 'testing backend',
            'html': f'<strong>Status: {message.status}, Jobs found: {message.jobs_found}</strong>'
        }
        
        resend.Emails.send(params)
    except Exception as e:
        print(f'Email failed: {e}')
        
def send_scrape_failed_email(user_id: str, message: ScrapeUpdateMessage):
    try:
        to_email = get_user_email(user_id)
        params: resend.Emails.SendParams = {
            'from': settings.test_from_email,
            'to': [to_email],
            'subject': 'backend failed',
            'html': f'<strong>Error message: {message.error_message}</strong>'
        }
        
        resend.Emails.send(params)
        
    except Exception as e:
        print(f'Email failed: {e}')
           
