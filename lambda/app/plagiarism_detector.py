import json
import boto3
import base64
import os
from io import BytesIO
from compiled_functions import get_one_one_matching_output, get_one_many_matching_output, add_output_data, add_input_database
from pypdf import PdfReader

print('Loading function')

s3_bucket = 'nus-sambaash'
s3_webis_data_filepath = 'plagiarism-detector/data/webis_db.csv'
s3_pdf_filepath = 'plagiarism-detector/data/pdfs'
s3_training_data_filepath = 'plagiarism-detector/data/train.csv'
s3_output_data_filepath = 'plagiarism-detector/data/output.csv'
sentbert_model_name = 'plagiarism-detector/models/trained_bert_model.joblib'
final_model_name = 'plagiarism-detector/models/final_model.joblib'
ngrams_lst = [1,4,5]

response_object = {}
response_object['headers'] = {}
response_object['headers']['Content-Type'] = 'application/json'
response_object['isBase64Encoded'] = False

def file_upload_1ton(event, context):
    s3_client = boto3.client('s3')
    file_content = event['body-json']
    filename = event["params"]["header"]["file_name"]
    userid = event["params"]["header"]["user_id"]
    content_decoded = base64.b64decode(file_content)
    filepath = os.path.join(s3_pdf_filepath, filename)
    s3_upload = s3_client.put_object(Bucket=s3_bucket, Key=filepath, Body=content_decoded)

    reader = PdfReader(BytesIO(content_decoded))
    text = ""

    for page in reader.pages:
        text += page.extract_text().replace('\n', ' ')

    add_input_database(userid, filename, text, s3_bucket, s3_webis_data_filepath )

    return {
        'statusCode': 200,
        'body': json.dumps(f'{filename} uploaded')
    }

def plagiarism_detector_1to1(event, context):
    try:
        event_dict = json.dumps(event)
        request_body = json.loads(event_dict)['body']
        
        user_id = json.loads(request_body)['user_id']
        input_doc_name = json.loads(request_body)['input_doc_name']
        source_doc_name = json.loads(request_body)['source_doc_name']

        response = get_one_one_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_doc_name, input_doc_name)

        add_output_data(user_id, input_doc_name, response, "1-1", s3_bucket, s3_output_data_filepath, source_doc_name)

        response_object['statusCode'] = 200
        response_object['body'] = json.dumps(response, default=str)
        
    except KeyError as e:
        response_object['statusCode'] = 400
        response_object['body'] = f"Missing input keys, please check your API input. {str(e)}"

    except Exception as e:
        response_object['statusCode'] = 500
        response_object['body'] = str(e)

    return response_object

def plagiarism_detector_1ton(event, context):
    try:
        event_dict = json.dumps(event)
        request_body = json.loads(event_dict)['body']
        
        user_id = json.loads(request_body)['user_id']
        input_doc_name = json.loads(request_body)['input_doc_name']

        response = get_one_many_matching_output(sentbert_model_name, final_model_name, ngrams_lst, input_doc_name)
        add_output_data(user_id, input_doc_name, response, "1-n", s3_bucket, s3_output_data_filepath, 'all')

        response_object['statusCode'] = 200
        response_object['body'] = json.dumps(response, default=str)
        
    except KeyError as e:
        response_object['statusCode'] = 400
        response_object['body'] = f"Missing input keys, please check your API input. {str(e)}"

    except Exception as e:
        response_object['statusCode'] = 500
        response_object['body'] = str(e)

    return response_object

