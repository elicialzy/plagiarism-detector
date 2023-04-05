### Custom Fields (need to insert)
[serverless.yml](serverless.yml)
line 19: SageMaker Excution Role
line 25: Name of SageMaker Training Job to copy from 
line 26: Prefix of subsequent training jobs

### Prerequisites

* Serverless is needed to deploy this code onto lambda

  * npm
    ```sh
    npm install -g serverless
    ```

  Configure AWS with relevant credentials
  * npm
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
