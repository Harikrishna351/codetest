import os
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_email(subject, message, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password, attachment_path=None):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    msg.attach(MIMEText(message, 'html'))

    if attachment_path:
        part = MIMEBase('application', 'octet-stream')
        with open(attachment_path, 'rb') as attachment:
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
        msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        print(f"Email sent to {to_email}.")
    except Exception as e:
        print(f"Error sending email: {e}")

def get_build_logs(build_id):
    client = boto3.client('codebuild')
    try:
        response = client.batch_get_builds(ids=[build_id])
        build = response['builds'][0]
        log_group_name = build['logs']['groupName']
        log_stream_name = build['logs']['streamName']

        logs_client = boto3.client('logs')
        log_events = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            startFromHead=True
        )
        log_content = "\n".join([event['message'] for event in log_events['events']])
        return log_content
    except Exception as e:
        print(f"Error retrieving build logs: {e}")
        return None

def save_logs_to_file(log_content, file_path):
    with open(file_path, 'w') as file:
        file.write(log_content)

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
    build_status = os.getenv('BUILD_STATUS')

    if not build_id:
        print("Build ID not found in environment variables.")
        return

    # Immediately retrieve and save build logs
    log_content = get_build_logs(build_id)
    log_file_path = "/tmp/build_logs.txt"
    if log_content:
        save_logs_to_file(log_content, log_file_path)

        if build_status == "SUCCEEDED":
            final_email_subject = f"CodeBuild Final Status for project {project_name}"
            final_email_body = f"""
            <p>Hi Team,</p>
            <p>The build for <strong>{project_name}</strong> has finished successfully.</p>
            <p>Build ID: {build_id}</p>
            <p>Status: <strong>SUCCEEDED</strong></p>
            <p>Build Logs: <a href="{log_file_path}">View Logs</a></p>
            """
        else:
            final_email_subject = f"CodeBuild Failed for project {project_name}"
            final_email_body = f"""
            <p>Hi Team,</p>
            <p>The build for <strong>{project_name}</strong> has failed.</p>
            <p>Build ID: {build_id}</p>
            <p>Status: <strong>FAILED</strong></p>
            <p>Build Logs: <a href="{log_file_path}">View Logs</a></p>
            """
        send_email(final_email_subject, final_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password, attachment_path=log_file_path)

if __name__ == '__main__':
    main()
