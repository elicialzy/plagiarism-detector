# Plagiarism Detection Dashboard Cloudwatch Metrics

## Description
This directory contains Python scripts to retrieve necessary Cloudwatch log data, adapt it to the format needed for QuickSight, and transfers the data to S3. It uses `boto3` to interact with the AWS Cloudwatch, S3 and Lambda services. The script performs the following actions:

## Folder Structure
```
dashboard/
├── getCloudwatchMetrics1to1.py 
├── getCloudwatchMetrics1ton.py 
```

## Details 
The details below are functions executed in the `getCloudwatchMetrics1to1.py` script to retrieve Cloudwatch metrics for the **1-1 matching** API service.

1.  Retrieve Cloudwatch metrics data for `plagiarism_1to1` Lambda function in the specified time period for the following metrics:
    -   Invocations
    -   Average Duration
    -   Maximum Duration
    -   Errors
2.  Format the metric data in a way that can be ingested by QuickSight.
3.  Upload the formatted metric data to the `nus-sambaash` S3 bucket in the following JSON files:
    -   invocations_1to1.json
    -   avg_duration_1to1.json
    -   highest_duration_1to1.json
    -   errors_1to1.json

## Usage
1.  Install the required libraries in requirements.txt
```
$ pip install -r requirements.txt
```
2.  Configure AWS CLI options  
```
$ aws configure
```  
3.  Run the Python script on your local machine
4.  Once the script is executed, it will retrieve the Cloudwatch metrics data, format it to be QuickSight compatible, and upload it to the `nus-sambaash` S3 bucket
5.  Upload the datasets to QuickSight for visualisation purposes
