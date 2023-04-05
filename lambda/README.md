# Plagiarism Detection Lambda Function

## Description
This directory contains AWS Lambda functions & Python dependencies for the 1-1 & 1-n plagiarism detection and document comparison service. The Lambda function can be deployed through container images uploaded on AWS ECR. There are 2 API services included:
- 1-1 matching
- 1-n matching

## Folder Structure
```
lambda/
├── Dockerfile  #Created using AWS's open-source base images
├── requirements.txt  #List of Python libraries needed
├── app/  
│   ├── nltk_data/  #NLTK library data
│   │   ├── stopwords   #Extracted from NLTK's stopwords library - nltk.download('stopwords')
│   │   ├──   ├── english   #List of NTTK's english stopwords
│   ├── compiled_functions.py   #All functions required
│   ├── plagiarism_detector.py   #Contains Lambda function handlers (plagiarism_detector_1to1 & plagiarism_detector_1ton)
│   ├── textmatcher.py   #Python's text-matcher library (https://github.com/JonathanReeve/text-matcher)
```

## Steps
The instructions below are for the **1-1 matching** API service. To deploy the **1-n matching** API service,
- Replace _plagiarism_detector_1to1_ with _plagiarism_detector_1ton_
- Replace _oneone_ image tag with _onemany_

1. Build docker image
```
$ docker build -t plagiarism_detector_1to1 .
```

2. Tag docker image with the Amazon ECR registry, repository, and image tag name
```
$ docker tag plagiarism_detector_1ton 630471847671.dkr.ecr.ap-southeast-1.amazonaws.com/plagiarism-detector:onemany
```

3. Push docker image to ECR
```
$ docker push 630471847671.dkr.ecr.ap-southeast-1.amazonaws.com/plagiarism-detector:onemany
```

4. Create Lambda function using ECR container image

- Note that the memory of Lambda function has to be minimally 512MB to support the sentence-transformers library

5. Build API Gateway REST API with Lambda proxy integration 

## API Documentation

### get_1to1_matches
<table>
  <tr>
    <th>API Name</th>
    <td>plagiarism_detector</td>
  </tr>
  <tr>
    <th>Description</th>
    <td>Get plagiarism flag, score and plagiarised texts, given 1 input document & ≥1 source documents</td>
  </tr>
  <tr>
    <th>API Endpoint</th>
    <td>https://rgbghnea40.execute-api.ap-southeast-1.amazonaws.com/dev/get_1to1_matches</td>
  </tr>
  <tr>
    <th>HTTP Method</th>
    <td>POST</td>
  </tr>
  <tr>
    <th>Authentication</th>
    <td>None</td>
  </tr>
</table>

Parameters  | Type | Description | Example
------------- | ------------- | ------------- | ------------- |
user_id | string | User ID | 'user_123'
input_doc_name  | string  | Name of input document  | 'file_num_123'
input_doc | string  | Text of input document  | ‘The castle is still so far perfect that the lower part is inhabited by a farmer's family’
source_docs | list[dict] |  List of dictionary(s) containing name of source document & text of input document | [{"source_doc_name": "file_num_456", "source_doc": "Castle is still as perfect as the bottom is inhabited by a farmer family.}]

**Sample Request**
```
{
    "user_id": "test_456_1to1",
    "input_doc_name": "input_file_5110",
    "input_doc": "Pride Russians suffered accordingly. While naturally precedes dramatic art poetry, drama, on the other hand, can achieve a degree of excellence where the theater is in a miserable state.",
    "source_docs": [
    {
      "source_doc_name": "source_file_5110",
      "source_doc": "The pride of the Russians did not suffer in consequence. While poetry naturally precedes dramatic art, the drama, on the other hand, cannot attain any degree of excellence where the theater is in such a miserable state"
    }
    ]
}
```
**Sample Response**
```
[
    {
        "input_doc_name": "input_file_5110",
        "plagiarism_flag": "0",
        "plagiarism_score": 0.4142616124291516,
        "plagiarised_text": [
            {
                "sentence": "Pride Russians suffered accordingly",
                "start_char_index": 1,
                "end_char_index": 35,
                "source_sentence": "The pride of the Russians did not suffer in consequence",
                "source_doc_name": "source_file_5110",
                "score": 0.747011661529541
            },
            {
                "sentence": "While naturally precedes dramatic art poetry, drama, on the other hand, can achieve a degree of excellence where the theater is in a miserable state",
                "start_char_index": 36,
                "end_char_index": 183,
                "source_sentence": "achieve degree of excellence where the theater is in a miserable state ",
                "source_doc_name": "source_file_5110",
                "score": 0.7736753693468769
            }
        ]
    }
]
```

### 1-n Matching
<table>
  <tr>
    <th>API Name</th>
    <td>plagiarism_detector</td>
  </tr>
  <tr>
    <th>Description</th>
    <td>Get plagiarism flag, score and plagiarised texts, given 1 input document. Cross checks with the database of documents stores in S3.</td>
  </tr>
  <tr>
    <th>API Endpoint</th>
    <td>https://rgbghnea40.execute-api.ap-southeast-1.amazonaws.com/dev/get_1ton_matches</td>
  </tr>
  <tr>
    <th>HTTP Method</th>
    <td>POST</td>
  </tr>
  <tr>
    <th>Authentication</th>
    <td>None</td>
  </tr>
</table>

Parameters  | Type | Description | Example
------------- | ------------- | ------------- | ------------- |
user_id | string | User ID | 'user_123'
input_doc_name  | string  | Name of input document  | 'file_num_123'
input_doc | string  | Text of input document  | ‘The castle is still so far perfect that the lower part is inhabited by a farmer's family’

**Sample Request**
```
{
    "user_id": "test_456”,
    "input_doc_name": "input_file_5110",
    "input_doc": "Pride Russians suffered accordingly. While naturally precedes dramatic art poetry, drama, on the other hand, can achieve a degree of excellence where the theater is in a miserable state."
  }
```

**Sample Response**
```
{
    "input_doc_name": "input_file_5110",
    "plagiarism_flag": "0",
    "plagiarism_score": 0.3526763034912935,
    "plagiarised_text": [
        {
            "sentence": "Pride Russians suffered accordingly",
            "start_char_index": 1,
            "end_char_index": 35,
            "source_sentence": "The pride of the Russians did not suffer in consequence",
            "source_doc_name": 4875,
            "score": 0.747011661529541
        },
        {
            "sentence": "While naturally precedes dramatic art poetry, drama, on the other hand, can achieve a degree of excellence where the theater is in a miserable state",
            "start_char_index": 36,
            "end_char_index": 183,
            "source_sentence": "achieve degree of excellence where the theater is in a miserable state ",
            "source_doc_name": 4875,
            "score": 0.7241072696029361
        }
    ]
}
```






