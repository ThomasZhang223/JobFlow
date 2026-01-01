import resend
from jinja2 import Template

from app.core.config import settings
from app.schemas.messages import ScrapeUpdateMessage
from app.schemas.database_tables import Preference
from app.services.database_service import get_user_email

resend.api_key = settings.resend_api_key

EMAIL_SUCCESS_TEMPLATE = """
<!doctype html>
<html lang="en">

<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <style media="all" type="text/css">
        .body {
            font-family: Helvetica, sans-serif;
            -webkit-font-smoothing: antialiased;
            font-size: 16px;
            line-height: 1.3;
            -ms-text-size-adjust: 100%;
            -webkit-text-size-adjust: 100%;
            background-color: #f4f5f6;
            margin: 0;
            padding: 20px;
            width: 100%;
        }

        .main {
            margin: 0 auto;
            max-width: 600px;
            background-color: #ffffff;
            border: 1px solid #eaebed;
            padding: 10px;
            border-radius: 16px;
        }

        .row {
            width: 100%;
        }

        .logo {
            position: absolute;
            top: 5%;
            left: 5%;
        }

        h1 {
            color: #009cde;
            font-size: 24px;
            margin-top: 20px;
            margin-bottom: 0px;
            text-align: center;
        }

        p {
            margin-top: 20px;
            margin-bottom: 0px;
            text-align: center;
        }

        .button {
            text-align: center;
            width: 100%;
        }

        .button table {
            width: auto;
            border: none;
        }

        .button table td {
            background-color: #ffffff;
            border: none;
        }

        .button a {
            line-height: 100%;
            text-align: center;
            padding: 12px 24px;
            line-height: 30px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 20px;
            box-sizing: border-box;
            display: inline-block;
            color: white;
            background-color: #009cde;
            text-decoration: none;
            transition: 0.3s ease;
            cursor: pointer;
            border-radius: 5px;
        }

        .button a:hover {
            background-color: #007aaf;
        }

        .footer {
            color: #9a9ea6;
            font-size: 16px;
            text-align: center;
        }
    </style>
</head>

<body>
    <section class="body" style="text-align: center">
        <table class="main" align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation" border="0">
            <tbody>
                <tr class="row">
                    <td style="text-align: center; vertical-align: middle;">
                       <h1>Your job scrape is complete!</h1>
<h3>We found <strong>{{ jobs_found }}</strong> jobs <br>matching your preferences</h3>
<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 5px">
              <strong>Search Criteria:</strong>
              <ul style:"list-style-type: none; padding: 0; margin: 0">
                  <li>Title: {{ preferences.title }}</li>
                  <li>Location: {{ preferences.location }}</li>
                  <li>Type: {{ preferences.job_type or 'Any' }}</li>
              </ul>
          </div>
<h3 style="margin-bottom:0px">Click this link to <br>check on your dashboard</h3>
<table class="button" align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation" border="0">
    <tbody>
        <tr>
            <td>
                <table align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation" border="0">
                    <tbody>
                        <tr>
                            <td>
                                <a href="{{ dashboard_url }}">Check Now</a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table>
                    </td>
                </tr>
            </tbody>
        </table>
        <table class="footer" align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation"
            border="0">
            <tbody>
                <tr class="row">
                    <td>
                        <p>Copyright &copy; 2025 JobFlow. All rights reserved.</p>
                    </td>
                </tr>
            </tbody>
        </table>
    </section>
</body>

</html>
"""

EMAIL_FAILURE_TEMPLATE = """
<!doctype html>
<html lang="en">

<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <style media="all" type="text/css">
        .body {
            font-family: Helvetica, sans-serif;
            -webkit-font-smoothing: antialiased;
            font-size: 16px;
            line-height: 1.3;
            -ms-text-size-adjust: 100%;
            -webkit-text-size-adjust: 100%;
            background-color: #f4f5f6;
            margin: 0;
            padding: 20px;
            width: 100%;
        }

        .main {
            margin: 0 auto;
            max-width: 600px;
            background-color: #ffffff;
            border: 1px solid #eaebed;
            padding: 10px;
            border-radius: 16px;
        }

        .row {
            width: 100%;
        }

        .logo {
            position: absolute;
            top: 5%;
            left: 5%;
        }

        h1 {
            color: #009cde;
            font-size: 24px;
            margin-top: 20px;
            margin-bottom: 0px;
            text-align: center;
        }

        p {
            margin-top: 20px;
            margin-bottom: 0px;
            text-align: center;
        }

        .button {
            text-align: center;
            width: 100%;
        }

        .button table {
            width: auto;
            border: none;
        }

        .button table td {
            background-color: #ffffff;
            border: none;
        }

        .button a {
            line-height: 100%;
            text-align: center;
            padding: 12px 24px;
            line-height: 30px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 20px;
            box-sizing: border-box;
            display: inline-block;
            color: white;
            background-color: #009cde;
            text-decoration: none;
            transition: 0.3s ease;
            cursor: pointer;
            border-radius: 5px;
        }

        .button a:hover {
            background-color: #007aaf;
        }

        .footer {
            color: #9a9ea6;
            font-size: 16px;
            text-align: center;
        }
    </style>
</head>

<body>
    <section class="body" style="text-align: center">
        <table class="main" align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation" border="0">
            <tbody>
                <tr class="row">
                    <td style="text-align: center; vertical-align: middle;">
                       <h1>Your job scrape has failed</h1>
<h3>We found <strong>{{ update.jobs_found }}</strong> jobs <br>before failure</h3>
<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 5px">
              <strong>Search Criteria:</strong>
              <ul style:"list-style-type: none; padding: 0; margin: 0">
                  <li>Title: {{ preferences.title }}</li>
                  <li>Location: {{ preferences.location }}</li>
                  <li>Type: {{ preferences.job_type or 'Any' }}</li>
              </ul>
          </div>
<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 5px">
              <strong>Error log:</strong>
              <ul>
                  <li>Error: {{ update.error_message }}</li>
              </ul>
          </div>
<h3 style="margin-bottom:0px">Click this link to <br>check on your dashboard</h3>
<table class="button" align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation" border="0">
    <tbody>
        <tr>
            <td>
                <table align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation" border="0">
                    <tbody>
                        <tr>
                            <td>
                                <a href="{{ dashboard_url }}">Check Now</a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table>
                    </td>
                </tr>
            </tbody>
        </table>
        <table class="footer" align="center" width="100%" cellpadding="0" cellspacing="0" role="presentation"
            border="0">
            <tbody>
                <tr class="row">
                    <td>
                        <p>Copyright &copy; 2025 JobFlow. All rights reserved.</p>
                    </td>
                </tr>
            </tbody>
        </table>
    </section>
</body>

</html>
"""

def send_scrape_complete_email(user_id: str, jobs_found: int, preferences: Preference):
    template = Template(EMAIL_SUCCESS_TEMPLATE)
    html_content = template.render(
        jobs_found=jobs_found,
        preferences=preferences,
        dashboard_url=settings.allowed_origins
    )
      
    try:
        to_email = get_user_email(user_id)
        params: resend.Emails.SendParams = {
            'from': f'JobFlow <{settings.test_from_email}>',
            'to': [to_email],
            'subject': 'testing backend',
            'html': html_content
        }
        
        resend.Emails.send(params)
    
    except Exception as e:
        print(f'Email failed: {e}')
        
def send_scrape_failed_email(user_id: str, update: ScrapeUpdateMessage, preferences: dict):
    template = Template(EMAIL_FAILURE_TEMPLATE)
    html_content = template.render(
        update=update,
        preferences=preferences,
        dashboard_url=settings.allowed_origins
    )
    
    try:
        to_email = get_user_email(user_id)
        params: resend.Emails.SendParams = {
            'from': f'JobFlow <{settings.test_from_email}>',
            'to': [to_email],
            'subject': 'Job Scraping Failed',
            'html': html_content
        }

        resend.Emails.send(params)

    except Exception as e:
        print(f'Email failed: {e}')
           
