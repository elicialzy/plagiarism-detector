# Plagiarism Detection Lambda Function

## Description
This directory contains AWS Lambda functions & Python dependencies for the 1-1 & 1-n plagiarism detection and document comparison service. The Lambda function can be deployed through container images uploaded on AWS ECR. There are 2 API services included:
- File upload
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
The instructions below are for the **1-1 matching** API service. To deploy the **1-n matching** or **file upload** API service,
- Replace `plagiarism_detector_1to1` with `plagiarism_detector_1ton` or `plagiarism_upload`
- Replace `oneone` image tag with `onemany` or `fileupload`

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

### 1. upload
`PUT /upload` - Upload PDF documents to S3
```
https://0d2tkz6x94.execute-api.ap-southeast-2.amazonaws.com/dev/upload
```
**Request Headers**
Parameters  | Type | Description | Example
------------- | ------------- | ------------- | ------------- |
Content-Type | string | Content type of request headers | 'application/pdf'
file_name  | string  | Filename of input document   | 'john_assignment1.pdf'
user_id | string  | User ID  | ‘john’

```
Content-Type: application/pdf
file_name : john_assignment1.pdf
user_id: john
```

**Response Body**
```
{
    "statusCode": 200,
    "body": "\"john_assignment1.pdf uploaded\""
}
```

### 2. get_1to1_matches
`POST /get_1to1_matches` - Given 2 documents, get plagiarism flag, score and plagiarised texts
```
https://rgbghnea40.execute-api.ap-southeast-1.amazonaws.com/dev/get_1to1_matches
```
**Request Body**
Parameters  | Type | Description | Example
------------- | ------------- | ------------- | ------------- |
user_id | string | User ID | 'jason'
input_doc_name  | string  | Filename of input document  | 'jason_assignment1.pdf'
source_doc_name | string  | Filename of source document  | ‘john_assignment1.pdf'

```
{
    "user_id": "jason",
    "input_doc_name": "jason_assignment1.pdf",
    "source_doc_name": "john_assignment1.pdf"
}
```

**Response Body**
```
{
    "input_doc_name": "jason_assignment1.pdf",
    "plagiarism_flag": "1",
    "plagiarism_score": 0.8223353227765466,
    "plagiarised_text": [
        {
            "sentence": "As is generally the case in the beginning of every nation's literature, any writer in Russia is taken for a miracle, and regarded with stupor",
            "start_char_index": 1,
            "end_char_index": 141,
            "source_sentence": " generally the case in the beginning of every nation's literature, any writer in Russia is taken for a miracle, and regarded with stupor ",
            "source_doc_name": "john_assignment1.pdf",
            "score": 0.9640488658284415
        },
        {
            "sentence": "The dramatist Kukolnik is an example of this",
            "start_char_index": 142,
            "end_char_index": 185,
            "source_sentence": "The dramatist Kukolnik is an example of this",
            "source_doc_name": "john_assignment1.pdf",
            "score": 1.0
        },
        {
            "sentence": "He has written a great deal for the theater, but nothing in him is to be praised so much as his zeal in imitation",
            "start_char_index": 186,
            "end_char_index": 298,
            "source_sentence": " written a great deal for the theater, but nothing in him is to be praised so much as his zeal in imitation ",
            "source_doc_name": "john_assignment1.pdf",
            "score": 0.9596398661682171
        }
    ]
}
```

### 3. get_1ton_matches
`POST /get_1ton_matches` - Given 1 document, check against documents database to get plagiarism flag, score and plagiarised texts
```
https://rgbghnea40.execute-api.ap-southeast-1.amazonaws.com/dev/get_1ton_matches
```
**Request Body**
Parameters  | Type | Description | Example
------------- | ------------- | ------------- | ------------- |
user_id | string | User ID | 'jason'
input_doc_name  | string  | Filename of input document  | 'jason_assignment1.pdf'

```
{
    "user_id": "jason",
    "input_doc_name": "jason_assignment1.pdf"
}
```

**Response Body**
```
{
    "input_doc_name": "jason_assignment1.pdf",
    "plagiarism_flag": "1",
    "plagiarism_score": 0.5822500902892679,
    "plagiarised_text": [
        {
            "sentence": "As is generally the case in the beginning of every nation's literature, any writer in Russia is taken for a miracle, and regarded with stupor",
            "start_char_index": 1,
            "end_char_index": 141,
            "source_sentence": " generally the case in the beginning of every nation's literature, any writer in Russia is taken for a miracle, and regarded with stupor ",
            "source_doc_name": "4875",
            "score": 0.9317157650164154
        },
        {
            "sentence": "The dramatist Kukolnik is an example of this",
            "start_char_index": 142,
            "end_char_index": 185,
            "source_sentence": "The dramatist Kukolnik is an example of this",
            "source_doc_name": "4875",
            "score": 1.000000238418579
        },
        {
            "sentence": "He has written a great deal for the theater, but nothing in him is to be praised so much as his zeal in imitation",
            "start_char_index": 186,
            "end_char_index": 298,
            "source_sentence": " written a great deal for the theater, but nothing in him is to be praised so much as his zeal in imitation ",
            "source_doc_name": "4875",
            "score": 0.9238026005035381
        }
    ]
}
```
