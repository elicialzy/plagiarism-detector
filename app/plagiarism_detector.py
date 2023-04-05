import json
from compiled_functions import get_one_one_matching_output, add_output_data

print('Loading function')

s3_bucket = 'nus-sambaash-2'
s3_training_data_filepath = 'plagiarism-detector/data/final_train.csv'
s3_output_data_filepath = 'plagiarism-detector/data/output.csv'
sentbert_model_name = 'plagiarism-detector/models/trained_bert_model.joblib'
final_model_name = 'plagiarism-detector/models/final_model.joblib'
ngrams_lst = [1,4,5]

def lambda_handler(event, context):
    response_object = {}
    response_object['headers'] = {}
    response_object['headers']['Content-Type'] = 'application/json'
    response_object['isBase64Encoded'] = False
    
    try:
        event_dict = json.dumps(event)
        request_body = json.loads(event_dict)['body']
        
        user_id = json.loads(request_body)['user_id']
        input_doc = json.loads(request_body)['input_doc']
        input_doc_name = json.loads(request_body)['input_doc_name']
        source_docs = json.loads(request_body)['source_docs']

        response = get_one_one_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_docs, input_doc, input_doc_name)

        add_output_data(user_id, source_docs, input_doc, input_doc_name, response, s3_bucket, s3_output_data_filepath)

        response_object['statusCode'] = 200
        response_object['body'] = json.dumps(response, default=str)
        
    except KeyError as e:
        response_object['statusCode'] = 400
        response_object['body'] = f"Missing input keys, please check your API input. {str(e)}"

    except Exception as e:
        response_object['statusCode'] = 500
        response_object['body'] = str(e)

    return response_object