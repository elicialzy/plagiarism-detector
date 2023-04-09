# plagiarism-detector

## Project Description
BT4103 Business Analytics Capstone Project on document comparison & plagiarism detection.

## Dataset Used
- Webis Crowd Paraphrase Corpus 2011 (https://webis.de/data/webis-cpc-11.html)

## General Flow of Project
![image](https://user-images.githubusercontent.com/65524472/230662351-8453671c-8214-433d-aa7e-f10d9cbdbbd8.png)
1. Text Preprocessing
- Documents are split into individual sentences and assigned indices. 
2. Direct Matching Detection
- Input text and source document is passed into our direct matching text function which generates the direct matching texts.
- A plagiarism score is computed by averaging the cosine similarity scores 
- `Output: Direct matching texts, plagiarism score from direct matching`
3. Paraphrased Text Detection 
- The non matching texts remaining are passed into our paraphrased text function with our sentence transformer model, generating the paraphrased output.
- A plagiarism score is computed from cosine similarity scores 
- `Output: Paraphrased texts, plagiarism score from paraphrased text detection`
4. Output From Text Generation Stage 
- Plagiarised texts are a concatenation of the 2 outputs from parts 2 and 3, the direct matching texts and paraphrased texts respectively. 
- The plagiarism scores from parts 2 and 3 are input as features into our ML Model which will generate a plagiarism flag and final plagiarism score. 
5. Feature Engineering
- From the preprocessed texts, we generate new features for our ML Model, namely the n-gram containment values and LCS score. This is in addition to the plagiarism scores generated from parts 2 and 3 as our features. 
6. Machine Learning Model 
- Our Logistic Regression Model which is trained on all these features then predicts whether the input is plagiarised. The probability of plagiarism as predicted by the model is our final plagiarism score. 
- `Output: Plagiarism Flag, Final Plagiarism Score`

## Folder Structure
```
dashboard/
├── getCloudwatchMetrics1to1.py
├── getCloudwatchMetrics1ton.py
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
[dashboard/](dashboard/) - Contains scripts to retrieve Cloudwatch log data to S3, and uploaded on QuickSight for visualisation purposes.

[lambda/](lambda/) - Contains scripts to deploy 1-1 and 1-n matching APIs on Lambda and API Gateway.

[retrain-codes//](retrain-codes/) - Contains scripts to set up an automated continuous learning pipeline for the custom BERT and Logistic Regression models on AWS Sagemaker.

## API Sample
### 1. upload
`PUT /upload`
```
https://0d2tkz6x94.execute-api.ap-southeast-2.amazonaws.com/dev/upload
```
**Request Headers**
```
Content-Type: application/pdf
file_name : john_assignment1.pdf
user_id: john
```

**Response**
```
{
    "statusCode": 200,
    "body": "\"john_assignment1.pdf uploaded\""
}
```

### 2. get_1to1_matches
`POST /get_1to1_matches`
```
https://0d2tkz6x94.execute-api.ap-southeast-2.amazonaws.com/dev/get_1to1_matches
```
**Request Body**
```
{
    "user_id": "test_123_1to1",
    "input_doc_name": "jason_assignment1.pdf",
    "source_doc_name": "john_assignment1.pdf"
}
```

**Response**
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
`POST /get_1ton_matches`
```
https://0d2tkz6x94.execute-api.ap-southeast-2.amazonaws.com/dev/get_1ton_matches
```
**Request Body**
```
{
    "user_id": "test_789_1to1",
    "input_doc_name": "jason_assignment1.pdf"
}
```

**Response**
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

## Dashboard
![image](https://user-images.githubusercontent.com/65524472/230664206-b353f877-5d55-41ec-9fdf-e54b115037af.png)
