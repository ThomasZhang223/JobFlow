from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from starlette.requests import Request
from starlette.responses import JSONResponse
from jinja2 import Template

from app.core.config import settings
from app.schemas.messages import ScrapeUpdateMessage
from app.schemas.database_tables import Preference
from app.services.database_service import get_user_email

EMAIL_SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Scrape Complete - JobFlow</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f6f9; color: #1a1a1a;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f6f9; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden;">
          <!-- Header -->
          <tr>
            <td style="padding: 40px 40px 20px 40px; text-align: center;">
              <div style="display: inline-block; padding: 12px 24px; border-width: 0px; margin-bottom: 24px;">
                <h1 style="margin: 0; color: #0a66c2; font-size: 50px; font-weight: 700; letter-spacing: 0.5px;">JobFlow</h1>
              </div>
              <h2 style="margin: 0 0 16px 0; color: #0077b5; font-size: 28px; font-weight: 600;">Job Scrape Complete!</h2>
              <p style="margin: 0; color: #1a1a1a; font-size: 20px; font-weight: 500;">We found <span style="color: #0077b5; font-weight: 700;">{{ jobs_found }} jobs</span> matching your preferences</p>
            </td>
          </tr>
          
          <!-- Search Criteria -->
          <tr>
            <td style="padding: 20px 40px;">
              <div style="background-color: #f8f9fb; border-radius: 8px; padding: 24px; border-left: 4px solid #0a66c2;">
                <h3 style="margin: 0 0 16px 0; color: #1a1a1a; font-size: 18px; font-weight: 600;">Search Criteria</h3>
                <table width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #5e6d82; font-size: 14px; font-weight: 500;">Title:</span>
                      <span style="color: #1a1a1a; font-size: 14px; margin-left: 8px;">{{ preferences.title }}</span>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #5e6d82; font-size: 14px; font-weight: 500;">Location:</span>
                      <span style="color: #1a1a1a; font-size: 14px; margin-left: 8px;">{{ preferences.location }}</span>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #5e6d82; font-size: 14px; font-weight: 500;">Type:</span>
                      <span style="color: #1a1a1a; font-size: 14px; margin-left: 8px;">{{ preferences.job_type or 'Any' }}</span>
                    </td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>
          
          <!-- CTA Section -->
          <tr>
            <td style="padding: 20px 40px 40px 40px; text-align: center;">
              <p style="margin: 0 0 24px 0; color: #1a1a1a; font-size: 16px; font-weight: 500;">Click the link below to view your new job matches</p>
              <a href="{{ dashboard_url }}" style="display: inline-block; background: #0077b5; color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(10, 102, 194, 0.3);">View Dashboard</a>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 24px 40px; background-color: #f8f9fb; border-top: 1px solid #e5e9f0; text-align: center;">
              <p style="margin: 0; color: #5e6d82; font-size: 12px;">Copyright © 2026 JobFlow. All rights reserved.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

EMAIL_FAILURE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Scrape Failed - JobFlow</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f6f9; color: #1a1a1a;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f6f9; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden;">
          <!-- Header -->
          <tr>
            <td style="padding: 40px 40px 20px 40px; text-align: center;">
              <div style="display: inline-block; padding: 12px 24px; border-width: 0px; margin-bottom: 24px;">
                <h1 style="margin: 0; color: #0a66c2; font-size: 50px; font-weight: 700; letter-spacing: 0.5px;">JobFlow</h1>
              </div>
              <h2 style="margin: 0 0 16px 0; color: #dc3545; font-size: 28px; font-weight: 600;">Job Scrape Failed</h2>
              <p style="margin: 0; color: #1a1a1a; font-size: 18px; font-weight: 500;">We found <span style="color: #dc3545; font-weight: 700;">{{ update.jobs_found }} jobs</span> before failure</p>
            </td>
          </tr>
          
          <!-- Search Criteria -->
          <tr>
            <td style="padding: 20px 40px;">
              <div style="background-color: #f8f9fb; border-radius: 8px; padding: 24px; border-left: 4px solid #0a66c2;">
                <h3 style="margin: 0 0 16px 0; color: #1a1a1a; font-size: 18px; font-weight: 600;">Search Criteria</h3>
                <table width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #5e6d82; font-size: 14px; font-weight: 500;">Title:</span>
                      <span style="color: #1a1a1a; font-size: 14px; margin-left: 8px;">{{ preferences.title }}</span>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #5e6d82; font-size: 14px; font-weight: 500;">Location:</span>
                      <span style="color: #1a1a1a; font-size: 14px; margin-left: 8px;">{{ preferences.location }}</span>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #5e6d82; font-size: 14px; font-weight: 500;">Type:</span>
                      <span style="color: #1a1a1a; font-size: 14px; margin-left: 8px;">{{ preferences.job_type or 'Any' }}</span>
                    </td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>
          
          <!-- Error Log -->
          <tr>
            <td style="padding: 0 40px 20px 40px;">
              <div style="background-color: #fff5f5; border-radius: 8px; padding: 24px; border-left: 4px solid #dc3545;">
                <h3 style="margin: 0 0 12px 0; color: #dc3545; font-size: 18px; font-weight: 600;">Error Details</h3>
                <p style="margin: 0; color: #5e6d82; font-size: 14px; line-height: 1.6;">{{ update.error_message }}</p>
              </div>
            </td>
          </tr>
          
          <!-- CTA Section -->
          <tr>
            <td style="padding: 20px 40px 40px 40px; text-align: center;">
              <p style="margin: 0 0 24px 0; color: #1a1a1a; font-size: 16px; font-weight: 500;">Check your dashboard for more details or try again</p>
              <a href="{{ dashboard_url }}" style="display: inline-block; background: #0077b5; color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(10, 102, 194, 0.3);">View Dashboard</a>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 24px 40px; background-color: #f8f9fb; border-top: 1px solid #e5e9f0; text-align: center;">
              <p style="margin: 0; color: #5e6d82; font-size: 12px;">Copyright © 2026 JobFlow. All rights reserved.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

conf = ConnectionConfig(
   MAIL_USERNAME="jobflow.vercel.app@gmail.com",
   MAIL_PASSWORD=settings.email_password,
   MAIL_FROM="jobflow.vercel.app@gmail.com",
   MAIL_PORT=587,
   MAIL_SERVER="smtp.gmail.com",
   MAIL_STARTTLS=True,
   MAIL_SSL_TLS=False,
)

async def send_scrape_complete_email(user_id: str, jobs_found: int, preferences: Preference):
    template = Template(MAIL_SUCCESS_TEMPLATE)
    html_content = template.render(
        jobs_found=jobs_found,
        preferences=preferences,
        dashboard_url=settings.allowed_origins
    )
      
    try:
        to_email = get_user_email(user_id)

        message = MessageSchema(
          subject="Your scrape is complete!",
          recipients=[to_email],
          body=html_content,
          subtype="html"
        )

        fm = FastMail(conf)
        await fm.send_message(message)
    
    except Exception as e:
        print(f'Email failed: {e}')
        
async def send_scrape_failed_email(user_id: str, update: ScrapeUpdateMessage, preferences: dict):
    template = Template(EMAIL_FAILURE_TEMPLATE)
    html_content = template.render(
        update=update,
        preferences=preferences,
        dashboard_url=settings.allowed_origins
    )
    
    try:
        to_email = get_user_email(user_id)

        message = MessageSchema(
          subject="Your scrape has failed",
          recipients=[to_email],
          body=html_content,
          subtype="html"
        )

        fm = FastMail(conf)
        await fm.send_message(message)

    except Exception as e:
        print(f'Email failed: {e}')
           
