import os
import boto3
import smtplib
from email.mime.text import MIMEText
import time

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

def get_pipeline_logs(pipeline_name, execution_id):
    # This function can be expanded to fetch logs from CloudWatch or other sources if needed
    return f"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline_name}/executions/{execution_id}/timeline"

def get_pipeline_status_from_logs(log_group_name, execution_id, interval=30):
    client = boto3.client('logs')
    query = f"fields @timestamp, @message | filter @message like /{execution_id}/ | sort @timestamp desc | limit 20"
    start_query_response = client.start_query(
        logGroupName=log_group_name,
        startTime=int(time.time()) - 3600,
        endTime=int(time.time()),
        queryString=query,
    )

    query_id = start_query_response['queryId']
    while True:
        response = client.get_query_results(queryId=query_id)
        if response['status'] == 'Complete':
            for result in response['results']:
                for field in result:
                    if field['field'] == '@message':
                        message = field['value']
                        if 'SUCCEEDED' in message:
                            return 'Succeeded'
                        elif 'FAILED' in message:
                            return 'Failed'
            return 'InProgress'
        time.sleep(interval)

def main():
    email_from = "harikarn10@gmail.com"
    email_to = "harikrishnatangelapally@gmail.com"
    smtp_server = "email-smtp.us-east-1.amazonaws.com"
    smtp_port = 587
    smtp_username = "AKIAS74TLYHELKOX7D74"
    smtp_password = "BOnvUFr8KQHsryZa3a/r2NRXSASK6UbhSpRIwLamvEZD"

    env = os.environ.get('ENV', 'np')
    project_name = os.getenv('CODEBUILD_PROJECT', f"codebuildtest-{env}")
    pipeline_name = os.getenv('PIPELINE_NAME')
    execution_id = os.getenv('CODEPIPELINE_EXECUTION_ID')
    log_group_name = f"/aws/codepipeline/{pipeline_name}"

    # Debugging statements to check environment variables
    print(f"Pipeline Name: {pipeline_name}")
    print(f"Execution ID: {execution_id}")
    print(f"Log Group Name: {log_group_name}")

    if not pipeline_name or not execution_id:
        print("Pipeline Name or Execution ID not found in environment variables.")
        return

    # Poll the pipeline status from CloudWatch logs
    pipeline_status = get_pipeline_status_from_logs(log_group_name, execution_id)

    if not pipeline_status:
        print("Failed to retrieve pipeline status.")
        return

    # Get pipeline logs URL
    log_url = get_pipeline_logs(pipeline_name, execution_id)

    if pipeline_status == "Succeeded":
        final_email_subject = f"CodePipeline Final Status for project {project_name}"
        final_email_body = f"""
        <p>Hi Team,</p>
        <p>The pipeline for <strong>{project_name}</strong> has finished successfully.</p>
        <p>Execution ID: {execution_id}</p>
        <p>Status: <strong>SUCCEEDED</strong></p>
        <p>Pipeline Logs: <a href="{log_url}">View Logs</a></p>
        """
    else:
        final_email_subject = f"CodePipeline Failed for project {project_name}"
        final_email_body = f"""
        <p>Hi Team,</p>
        <p>The pipeline for <strong>{project_name}</strong> has failed.</p>
        <p>Execution ID: {execution_id}</p>
        <p>Status: <strong>FAILED</strong></p>
        <p>Pipeline Logs: <a href="{log_url}">View Logs</a></p>
        """
    send_email(final_email_subject, final_email_body, email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password)

if __name__ == '__main__':
    main()
