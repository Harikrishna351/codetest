import os
import time
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

def get_build_status(build_id):
    client = boto3.client('codebuild')
    try:
        response = client.batch_get_builds(ids=[build_id])
        builds = response['builds']
        if builds:
            build_info = builds[0]
            return {
                'buildStatus': build_info['buildStatus'],
                'currentPhase': build_info['currentPhase'],
                'endTime': build_info.get('endTime', 'Still Running'),
                'buildNumber': build_info['buildNumber']
            }
        else:
            return {'buildStatus': 'UNKNOWN'}
    except Exception as e:
        print(f"Error retrieving build status: {e}")
        return {'buildStatus': 'UNKNOWN'}

def main():
    email_from = "harikarn10@gmail.com"
    email_to = "harikrishnatangelapally@gmail.com"
    smtp_server = "email-smtp.us-east-1.amazonaws.com"
    smtp_port = 587
    smtp_username = "AKIAS74TLYHELKOX7D74"
    smtp_password = "BOnvUFr8KQHsryZa3a/r2NRXSASK6UbhSpRIwLamvEZD"

    env = os.environ.get('ENV', 'np')  # Default environment
    project_name = os.environ.get('CODEBUILD_PROJECT', f"codebuildtest-{env}")
    build_id = os.environ.get('CODEBUILD_BUILD_ID')  # This should be set by CodeBuild

    if not build_id:
        print("Build ID not found in environment variables.")
        return

    print(f"Using Project Name: {project_name}")
    print(f"Using Build ID: {build_id}")

    # Send initial email that the build is in progress
    email_subject = f"CodeBuild Alert for project {project_name}"
    email_body = f"""
    <p>Hi Team,</p>
    <p>The build for <strong>{project_name}</strong> is currently <strong>IN_PROGRESS</strong>.</p>
    <p>Build ID: {build_id}</p>
    """
    send_email(email_subject, email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)

    # Poll build status until it's no longer "IN_PROGRESS"
    build_status = get_build_status(build_id)
    while build_status == 'IN_PROGRESS':
        print("Build is still in progress. Waiting for status to change...")
        build_status = get_build_status(build_id)

    print(f"Final Build Status: {build_status}")

    # Prepare the final email body
    final_email_subject = f"CodeBuild Final Status for project {project_name}"
    final_email_body = f"""
    <p>Hi Team,</p>
    <p>The build for <strong>{project_name}</strong> has finished.</p>
    <p>Build ID: {build_id}</p>
    <p>Status: <strong>{build_status}</strong></p>
    """

    # Send email with final build status
    print(f'Sending final email for project: {project_name} with final status: {build_status}')
    send_email(final_email_subject, final_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)

if __name__ == '__main__':
    main()
