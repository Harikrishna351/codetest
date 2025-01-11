import os
import time
import boto3
import sys
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
            return builds[0]['buildStatus']
        else:
            return 'UNKNOWN'
    except Exception as e:
        print(f"Error retrieving build status: {e}")
        return 'UNKNOWN'

def get_build_logs(build_id):
    client = boto3.client('codebuild')
    try:
        logs = client.batch_get_builds(ids=[build_id])
        return logs['builds'][0]['logs']['deepLink']
    except Exception as e:
        print(f"Error retrieving build logs: {e}")
        return None

def save_logs_to_file(log_url, file_path):
    # Here you would typically fetch the logs from the log URL
    with open(file_path, 'w') as file:
        file.write(f"Log URL: {log_url}\n")
        # Simulate some log content
        file.write("Build completed successfully.\n")  # Simulate successful log content

def read_logs_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

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
        sys.exit(1)

    # Check initial build status
    build_status = get_build_status(build_id)
    print(f"Current build status: {build_status}")

    # Send IN_PROGRESS email if the build is currently in progress
    if build_status == 'IN_PROGRESS':
        in_progress_email_subject = f"CodeBuild In Progress for project {project_name}"
        in_progress_email_body = f"""
        <p>Hi Team,</p>
        <p>The build for <strong>{project_name}</strong> is currently in progress.</p>
        <p>Build ID: {build_id}</p>
        <p>Status: <strong>{build_status}</strong></p>
        """
        send_email(in_progress_email_subject, in_progress_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)

    # Immediately retrieve and save build logs
    log_url = get_build_logs(build_id)
    if log_url:
        log_file_path = "build_logs.txt"
        save_logs_to_file(log_url, log_file_path)

        # Read the logs from the file
        log_content = read_logs_from_file(log_file_path)
        print("Log content read from file:")
        print(log_content)

        # Determine final email based on build status
        if build_status == 'SUCCEEDED':
            final_email_subject = f"CodeBuild Final Status for project {project_name}"
            final_email_body = f"""
            <p>Hi Team,</p>
            <p>The build for <strong>{project_name}</strong> has finished successfully.</p>
            <p>Build ID: {build_id}</p>
            <p>Status: <strong>{build_status}</strong></p>
            <p>Build Logs: <a href="{log_url}">View Logs</a></p>
            """
            send_email(final_email_subject, final_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)
        else:
            failed_email_subject = f"CodeBuild Failed for project {project_name}"
            failed_email_body = f"""
            <p>Hi Team,</p>
            <p>The build for <strong>{project_name}</strong> has failed.</p>
            <p>Build ID: {build_id}</p>
            <p>Status: <strong>{build_status}</strong></p>
            <p>Build Logs: <a href="{log_url}">View Logs</a></p>
            """
            send_email(failed_email_subject, failed_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)

if __name__ == '__main__':
    main()
