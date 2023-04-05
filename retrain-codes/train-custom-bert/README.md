### Prerequisites (which have already been done)

S3 bucket with training data in nus-sambaash/plagiarism-detector/data/train.csv

### Instructions - 

1. Upload this folder onto an Amazon Sagemaker Notebook Instance
2. Create ECR repository with name 'custom-sentence-transformer'
3. Add permissions to ECR repository to allow SageMaker to upload images to ECR
```
"Action": [
  "ecr:BatchCheckLayerAvailability",
  "ecr:BatchGetImage",
  "ecr:CompleteLayerUpload",
  "ecr:GetDownloadUrlForLayer",
  "ecr:InitiateLayerUpload",
  "ecr:PutImage",
  "ecr:UploadLayerPart"
]
```
4. Run all cells in [run_scripts.ipynb](/run_scripts.ipynb)
5. Create Training Job
```
Job Name : custom-bert-base
Algorithm options > Provide Container ECR path : <path-to-repository-created-above>
Input data configuration > training > Channel name : 'training'
Input data configuration > training > Data source : S3
Input data configuration > training > S3 location : 's3://nus-sambaash/plagiarism-detector/data/train.csv'
Output data configuration : 's3://nus-sambaash/plagiarism-detector/training-jobs'
```
6. The trained model from this training job should reside in s3://nus-sambaash/plagiarism-detector/training-jobs/custom-bert-base/output/model.tar.gz'
