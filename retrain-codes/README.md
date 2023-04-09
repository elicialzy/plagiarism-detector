# Plagiarism Detection Continuous Learning Pipeline

## Description
This directory contains the necessary codes and instructions to set up an automated continuous learning pipeline in AWS sagemaker. There are 2 sub-pipelines involved:
* custom-ml
* custom-bert

## Folder Structure
```
retrain-codes/
├── assets 
│   ├── df10.csv
│   ├── final_train.csv
├── lambda-custom-bert
│   ├── handler.py
│   ├── serverless.yml
├── lambda-custom-ml
│   ├── handler.py
│   ├── serverless.yml
├── train-custom-bert
│   ├── container/
│   │   ├── codes   
│   │   ├──   ├── train    
│   │   ├── Dockerfile
│   │   ├── build_and_push.sh   
│   ├── run_scripts.ipynb
├── train-custom-ml
│   ├── container/
│   │   ├── codes   
│   │   ├──   ├── train    
│   │   ├── Dockerfile
│   │   ├── build_and_push.sh   
│   ├── run_scripts.ipynb
```

## Directory
[assets/](assets/) - contains necessary datasets for testing the continuous learning pipeline

[lambda-custom-bert/](lambda-custom-bert/) - contains scripts for deploying lambda function to trigger SageMaker Training Job for our custom BERT model

[lambda-custom-ml/](lambda-custom-ml/) - contains scripts for deploying lambda function to trigger SageMaker Training Job for our custom logistic regression model

[train-custom-bert/](train-custom-bert/) - contains scripts for dockerizing BERT model training and uploading it onto ECR

[train-custom-ml/](train-custom-ml/) - contains scripts for dockerizing logistic regression model training and uploading it onto ECR

## Steps
1. Follow the steps in [train-custom-bert/README.md](train-custom-bert/README.md)
2. Follow the steps in [train-custom-ml/README.md](train-custom-ml/README.md)
3. Create AWS SNS Standard topic. No special configuration is needed.
4. Create Event Notification for nus-sambaash bucket via `nus-sambaash` > `Properties` > `Event Notification`
```
Prefix : plagiarism-detector/
Suffix : data/train.csv
Event Types: select suitable events, for testing we need to select the s3:ObjectCreated:CompleteMultipartUpload event.
Destination: select 'SNS Topic' and select the SNS topic created in Step 3
```
5. Follow the steps in [lambda-custom-bert/README.md](lambda-custom-bert/README.md)
6. Follow the steps in [lambda-custom-ml/README.md](lambda-custom-ml/README.md)
7. For the lambda functions created in 5 and 6, add SNS trigger and select the SNS topic created in Step 3

## Test
1. Replace `s3://nus-sambaash/plagiarism-detector/data/train.csv` with [assets/df10.csv]([assets/df10.csv]) (a subset of the original dataset) to test if training jobs can be completed. Make sure to rename the file to `train.csv` so that it can be identified by the training job.
2. This upload of file should trigger S3 to send a notification to SNS and trigger the Lambda function to create a new training job.
3. Post-testing: Replace s3://nus-sambaash/plagiarism-detector/data/train.csv dataset with [assets/final_train.csv](assets/final_train.csv) and rename the file to `train.csv` after testing

