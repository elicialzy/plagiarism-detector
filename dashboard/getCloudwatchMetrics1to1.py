import json
import boto3
from datetime import datetime


def update_metric_data():
    """
    Retrieves the necessary Cloudwatch log data, adapting it for the format we want for QuickSight,
    transfer the data to S3. 

    """
    cloudwatch = boto3.client("cloudwatch")
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id':'invocations',
                'MetricStat': {
                    'Metric': {
                        "Namespace": "AWS/Lambda",
                        "MetricName": "Invocations",
                        "Dimensions": [
                            {
                                "Name": "FunctionName",
                                "Value": "plagiarism_1to1"
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum'
                }
            },
            {
                'Id':'duration',
                'MetricStat': {
                    'Metric': {
                        "Namespace": "AWS/Lambda",
                        "MetricName": "Duration",
                        "Dimensions": [
                            {
                                "Name": "FunctionName",
                                "Value": "plagiarism_1to1"
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average'
                }
            },
            {
                'Id':'max_duration',
                'MetricStat': {
                    'Metric': {
                        "Namespace": "AWS/Lambda",
                        "MetricName": "Duration",
                        "Dimensions": [
                            {
                                "Name": "FunctionName",
                                "Value": "plagiarism_1to1"
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Maximum'
                }
            },
            {
                'Id':'error',
                'MetricStat': {
                    'Metric': {
                        "Namespace": "AWS/Lambda",
                        "MetricName": "Error",
                        "Dimensions": [
                            {
                                "Name": "FunctionName",
                                "Value": "plagiarism_1to1"
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average'
                }
            }
        ],
        StartTime=datetime(2023, 4, 6),
        EndTime=datetime(2023, 4, 8)
    )

    overall_jsons_list = [format_metric_data(metric_data) for metric_data in response["MetricDataResults"]]
    
    json_names = ["invocations_1to1.json", "avg_duration_1to1.json", "highest_duration_1to1.json", "errors_1to1.json"]
    for i, json_name in enumerate(json_names):
        write_json(overall_jsons_list[i], json_name)
    
def format_metric_data(metric_data):
    """
    Converts Cloudwatch response JSON into a format that can be ingested by QuickSight
    """
    json_list = [{"value": value, "time": timestamp.isoformat()} 
                 for value, timestamp in zip(metric_data["Values"], metric_data["Timestamps"])]
    return json_list

def write_json(new_json_data, fname):
    """
    Upload reformatted JSON data to S3 Sambaash Dashboard bucket, given the JSON data and corresponding filename.
    """
    s3_client = boto3.client("s3")
    s3 = boto3.resource("s3")
    S3_BUCKET_NAME = 'nus-sambaash'
    object_key = "plagiarism-detector-dashboard-1to1/" + fname
    
    # Check if the object already exists in S3 bucket
    try:
        s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=object_key)
    except s3_client.exceptions.NoSuchKey:
        # If the object does not exist, create it
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=object_key, Body=b'')
            
    s3_object = s3.Object(S3_BUCKET_NAME, object_key)
    json_byte = json.dumps(new_json_data).encode('UTF-8')
    s3_object.put(Body=json_byte, ContentType='application/json')


def lambda_handler(event, context):
    return update_metric_data()
    


event = []
context = []
lambda_handler(event, context)
