# Plagiarism Detection Lambda Function

## Description
This directory contains AWS Lambda functions & Python dependencies for the 1-1 & 1-n plagiarism detection and document comparison service. The Lambda function can be deployed through container images uploaded on AWS ECR. There are 2 API services included:
- get_1to1_matches
- get_1ton_matches

## Folder Structure
```
lambda/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── nltk_data/
│   │   ├── stopwords
│   │   ├──   ├── english        
│   ├── compiled_functions.py
│   ├── plagiarism_detector.py
│   ├── textmatcher.py
```