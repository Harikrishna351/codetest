import smtplib
import os
import boto3
from email.mime.text import MIMEText

def send_email(subject, message):
    smtp_server = "email-smtp.us-east-1.amazonaws.com"  # Your SMTP server
    smtp_port = 587
    smtp_username = "AKIAS74TLYHELKOX7D74"  # Replace with your SMTP username
    smtp_password = "BOnvUFr8KQHsryZa3a/r2NRXSASK6UbhSpRIwLamvEZD"  # Replace with your SMTP password
    from_email = "harikarn10@gmail.com"  # Replace with your email
    to_email = "harikrishnatangelapally@gmail.com"  # Replace with recipient email

    # Create the email
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())

def get_build_status(build_id):
    client = boto3.client('codebuild')
    try:
        response = client.batch_get_builds(ids=[build_id])
        builds = response['builds']
        if builds:
            build_info = builds[0]
            return {
                'buildStatus': build_info['buildStatus'],
                'currentState': build_info['currentState'],
                'buildNumber': build_info['buildNumber']
            }
        else:
            return {'buildStatus': 'UNKNOWN'}
    except Exception as e:
        print(f"Error retrieving build status: {e}")
        return {'buildStatus': 'UNKNOWN'}
def wait_for_build_completion(build_id, poll_interval=5):
    client = boto3.client('codebuild')
    while True:
        build_info = get_build_status(build_id)
        build_status = build_info.get('buildStatus', 'UNKNOWN')
        
        if build_status not in ['IN_PROGRESS', 'UNKNOWN']:
            return build_info  # Return final build info once it's not in progress
        
        print(f"Current build status: {build_status}. Waiting...")
        time.sleep(poll_interval)  # Wait for a bit before polling again
# Inside the main function where you send the email

if __name__ == "__main__":
    build_id = os.environ.get('CODEBUILD_BUILD_ID')
    build_info = wait_for_build_completion(build_id) if build_id else {'buildStatus': 'UNKNOWN'}
    
    # Accessing build information with correct keys
    build_number = build_info.get('buildNumber', 'UNKNOWN')
    build_status = build_info.get('buildStatus', 'UNKNOWN')
    current_phase = build_info.get('currentPhase', 'N/A')
    end_time = build_info.get('endTime', 'N/A')

    subject = f"CodeBuild Status: {build_status}"
    message = (
        f"The CodeBuild job #{build_number} finished with status: {build_status}.\n"
        f"Current Phase: {current_phase}\n"
        f"End Time: {end_time}"
    )
    send_email(subject, message)
