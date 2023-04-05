### Custom Fields (don't need to change for testing)
[container/codes/train](container/codes/train)

* [line 56](https://github.com/elicialzy/plagiarism-detector/blob/4294194b6c587bb9561bd5c43b9d0ac91b981a6c/retrain-codes/train-custom-ml/container/codes/train#L56) - `BERTMODEL_BUCKET`: bucket where the pre-trained custom sentence transformer model resides

* [line 57](https://github.com/elicialzy/plagiarism-detector/blob/4294194b6c587bb9561bd5c43b9d0ac91b981a6c/retrain-codes/train-custom-ml/container/codes/train#L57) - `BERTMODEL_PATH`: path where the pre-trained custom sentence transformer model resides

### Prerequisites (which have already been done)

S3 bucket with training data in `nus-sambaash/plagiarism-detector/data/train.csv`
S3 bucket with pre-trained sentence bert model in `nus-sambaash/plagiarism-detector/models/trained_bert_model.joblib`

### Instructions - 

1. Upload this folder onto an Amazon Sagemaker Notebook Instance
2. Create ECR repository with name `custom-ml`
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
4. Run all cells in [run_scripts.ipynb](run_scripts.ipynb)
5. Create Training Job
```
Job Name : custom-ml-base
Algorithm options > Provide Container ECR path : <path-to-repository-created-above>
Input data configuration > training > Channel name : 'training'
Input data configuration > training > Data source : S3
Input data configuration > training > S3 location : 's3://nus-sambaash/plagiarism-detector/data/train.csv'
Output data configuration : 's3://nus-sambaash/plagiarism-detector/training-jobs'
```
6. The trained model from this training job should reside in s3://nus-sambaash/plagiarism-detector/training-jobs/custom-ml-base/output/model.tar.gz'
