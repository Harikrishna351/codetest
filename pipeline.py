import os
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import json

def send_email(subject, message, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    msg.attach(MIMEText(message, 'html'))

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
        if response['pipelineExecutionSummaries']:
            latest_execution = response['pipelineExecutionSummaries'][0]
            return latest_execution['status'], latest_execution['pipelineExecutionId']
        else:
            print("No executions found for the pipeline.")
            return None, None
    except Exception as e:
        print(f"Error retrieving pipeline status: {e}")
        return None, None

def poll_pipeline(pipeline_name, interval=15):
    client = boto3.client('codepipeline')
    
    while True:  # Continuous polling until a terminal state is reached
        try:
            response = client.get_pipeline_state(name=pipeline_name)
            statuses = [
                stage['latestExecution']['status']
                for stage in response['stageStates']
                if 'latestExecution' in stage
            ]
            print(f"Current pipeline statuses: {statuses}")
            
            if any(status == 'FAILED' for status in statuses):
                print("Pipeline has failed.")
                return 'FAILED'
            elif all(status == 'SUCCEEDED' for status in statuses):
                print("Pipeline completed successfully.")
                return 'SUCCEEDED'
        except Exception as e:
            print(f"Error fetching pipeline status: {e}")
            return None
        
        time.sleep(interval)  # Wait before the next check

def get_pipeline_state(pipeline_name):
    client = boto3.client('codepipeline')
    try:
        response = client.get_pipeline_state(name=pipeline_name)
        return response
    except Exception as e:
        print(f"Error fetching pipeline state: {e}")
        return None

def main():
    email_from = "harikarn10@gmail.com"
    email_to = "harikrishnatangelapally@gmail.com"
    smtp_server = "email-smtp.us-east-1.amazonaws.com"
    smtp_port = 587
    smtp_username = "AKIAS74TLYHELKOX7D74"
    smtp_password = "BOnvUFr8KQHsryZa3a/r2NRXSASK6UbhSpRIwLamvEZD"

    env = os.environ.get('ENV', 'np')
    project_name = os.getenv('CODEBUILD_PROJECT', f"test2-{env}")
    pipeline_name = os.getenv('PIPELINE_NAME')

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
        print("Pipeline completed successfully.")

    # Fetch and print the pipeline state
    pipeline_state = get_pipeline_state(pipeline_name)
    if pipeline_state:
        print(json.dumps(pipeline_state, indent=4, sort_keys=True))
    else:
        print("Failed to retrieve pipeline state.")

if __name__ == '__main__':
    main()
