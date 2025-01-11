import os
import boto3
import smtplib
from email.mime.text import MIMEText

def send_email(subject, message, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        print(f"Email sent to {to_email}.")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    email_from = "harikarn10@gmail.com"
    email_to = "harikrishnatangelapally@gmail.com"
    smtp_server = "email-smtp.us-east-1.amazonaws.com"
    smtp_port = 587
    smtp_username = "AKIAS74TLYHELKOX7D74"
    smtp_password = "BOnvUFr8KQHsryZa3a/r2NRXSASK6UbhSpRIwLamvEZD"

    env = os.environ.get('ENV', 'np')
    project_name = os.getenv('CODEBUILD_PROJECT', f"codebuildtest-{env}")
    build_id = os.getenv('CODEBUILD_BUILD_ID')

    if not build_id:
        print("Build ID not found in environment variables.")
        return

    in_progress_email_subject = f"CodeBuild In Progress for project {project_name}"
    in_progress_email_body = f"""
    <p>Hi Team,</p>
    <p>The build for <strong>{project_name}</strong> is currently in progress.</p>
    <p>Build ID: {build_id}</p>
    <p>Status: <strong>IN_PROGRESS</strong></p>
    """
    send_email(in_progress_email_subject, in_progress_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)

if __name__ == '__main__':
    main()
