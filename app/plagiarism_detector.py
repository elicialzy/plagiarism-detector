import json
from compiled_functions import get_one_one_matching_output, get_one_many_matching_output

print('Loading function')

s3_bucket = 'nus-sambaash-data'
s3_training_data_filepath = 'plagiarism-detector/webis_db.csv'
sentbert_model_name = 'models/trained_bert_model.joblib'
final_model_name = 'models/final_model.joblib'
ngrams_lst = [1,4,5]

def lambda_handler(event, context):
    try:
        input_doc = event['input_doc']
        input_doc_name = event['input_doc_name']
        source_docs = event['source_docs']
        matching_type = event['matching_type'] 

        if matching_type == '1-1':
            response = get_one_one_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_docs, input_doc, input_doc_name)
        else:
            response = get_one_many_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_docs, input_doc, input_doc_name)

        response_object = {
            'status_code': 200,
            'success': True,
            'body': json.loads(json.dumps(response, default=str))
        }

    except KeyError as e:
        response_object = {
            'status_code': 400,
            'success': False,
            'body': "Missing input keys, please check your API input."
        }
        
    except Exception as e:
        response_object = {
            'status_code': 500,
            'success': False,
            'body': str(e)

        }


    return response_object