import os
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time

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

def get_pipeline_status(pipeline_name):
    client = boto3.client('codepipeline')
    try:
        response = client.list_pipeline_executions(pipelineName=pipeline_name)
        # Get the latest execution
        latest_execution = response['pipelineExecutionSummaries'][0]
        return latest_execution['status'], latest_execution['pipelineExecutionId']
    except Exception as e:
        print(f"Error retrieving pipeline status: {e}")
        return None, None

def poll_pipeline(pipeline_name, max_retries=5, interval=15):
    client = boto3.client('codepipeline')
    for attempt in range(max_retries):
        try:
            response = client.get_pipeline_state(name=pipeline_name)
            statuses = [
                stage['latestExecution']['status']
                for stage in response['stageStates']
                if 'latestExecution' in stage
            ]
            print(f"Attempt {attempt + 1}: Current pipeline statuses - {statuses}")
            if all(status in ['SUCCEEDED', 'FAILED'] for status in statuses):
                print(f"Pipeline completed with statuses: {statuses}")
                return statuses
        except Exception as e:
            print(f"Error fetching pipeline status: {e}")
            return
        time.sleep(interval)

def main():
    email_from = "harikarn10@gmail.com"
    email_to = "harikrishnatangelapally@gmail.com"
    smtp_server = "email-smtp.us-east-1.amazonaws.com"
    smtp_port = 587
    smtp_username = "AKIAS74TLYHELKOX7D74"
    smtp_password = "BOnvUFr8KQHsryZa3a/r2NRXSASK6UbhSpRIwLamvEZD"

    env = os.environ.get('ENV', 'np')
    project_name = os.getenv('CODEBUILD_PROJECT', f"test2-{env}")
    pipeline_name = os.getenv('PIPELINE_NAME')  # Assuming the pipeline name matches the repo name

    if not pipeline_name:
        print("Pipeline Name not found in environment variables.")
        return

    # Poll the pipeline status
    pipeline_result = poll_pipeline(pipeline_name)

    if pipeline_result == 'FAILED':
        # Fetch the latest execution ID
        final_status, execution_id = get_pipeline_status(pipeline_name)
        if execution_id:
            final_email_subject = f"CodePipeline Failed for project {project_name}"
            final_email_body = f"""
            <p>Hi Team,</p>
            <p>The pipeline for <strong>{project_name}</strong> has failed.</p>
            <p>Execution ID: {execution_id}</p>
            <p>Status: <strong>FAILED</strong></p>
            <p>Please check the AWS CodePipeline console for more details.</p>
            """
            send_email(final_email_subject, final_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)
    else:
        print("Pipeline completed successfully or did not fail.")

if __name__ == '__main__':
    main()
