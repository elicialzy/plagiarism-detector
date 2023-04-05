### Custom Fields to update
[serverless.yml](serverless.yml)
[line 19](https://github.com/elicialzy/plagiarism-detector/blob/7d31029ccde33f4b62f3b8ac20ea31c76ea50558/retrain-codes/lambda-custom-ml/serverless.yml#L19): SageMaker Excution Role
[line 25](https://github.com/elicialzy/plagiarism-detector/blob/7d31029ccde33f4b62f3b8ac20ea31c76ea50558/retrain-codes/lambda-custom-ml/serverless.yml#L25): Name of SageMaker Training Job to copy from
[line 26](https://github.com/elicialzy/plagiarism-detector/blob/7d31029ccde33f4b62f3b8ac20ea31c76ea50558/retrain-codes/lambda-custom-ml/serverless.yml#L26): Prefix of subsequent training jobs

### Prerequisites

* Serverless is needed to deploy this code onto lambda

  * npm
    ```sh
    npm install -g serverless
    ```

  Configure AWS with relevant credentials
  * aws
    ```sh
    aws configure
    ```

* Previous manually created SageMaker Training Job
* SNS trigger upon update of S3 training data

### Instructions

1. Navigate into this folder directory
2. Deploy the code
   ```sh
   serverless deploy
   ```
