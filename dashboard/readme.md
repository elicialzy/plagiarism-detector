# getCloudwatchMetrics1to1 and getCloudwatchMetrics1ton Python functions

This Python script retrieves necessary Cloudwatch log data, adapts it to the format needed for QuickSight, and transfers the data to S3. It uses `boto3` to interact with the AWS Cloudwatch, S3 and Lambda services. The script performs the following actions:

## getCloudwatchMetrics1to1

1.  Retrieves Cloudwatch metrics data for `plagiarism_1to1` Lambda function in the specified time period for the following metrics:
    -   Invocations
    -   Average Duration
    -   Maximum Duration
    -   Errors
2.  Formats the metric data in a way that can be ingested by QuickSight.
3.  Uploads the formatted metric data to the `nus-sambaash` S3 bucket in the following JSON files:
    -   invocations_1to1.json
    -   avg_duration_1to1.json
    -   highest_duration_1to1.json
    -   errors_1to1.json
   ## getCloudwatchMetrics1ton
   1.  Retrieves Cloudwatch metrics data for `plagiarism_1ton` Lambda function in the specified time period for the following metrics:
    -   Invocations
    -   Average Duration
    -   Maximum Duration
    -   Errors
2.  Formats the metric data in a way that can be ingested by QuickSight.
3.  Uploads the formatted metric data to the `nus-sambaash` S3 bucket in the following JSON files:
    -   invocations_1ton.json
    -   avg_duration_1ton.json
    -   highest_duration_1ton.json
    -   errors_1ton.json

## Requirements

This script requires the following libraries to be installed:

-   `boto3`
-   `datetime`
-   `json`

## Usage

1.  Install the required libraries by running the following command:
    
    
    
    `pip install boto3 datetime json` 
    
2.  Make sure you have AWS credentials configured on your system.
3.  Run the Python script on your local machine.
4.  Once the script is executed, it will retrieve the Cloudwatch metrics data, format it to be QuickSight compatible, and upload it to the `nus-sambaash` S3 bucket.