import json
from compiled_functions import get_one_one_matching_output, get_one_many_matching_output

print('Loading function')

sentbert_model_name = 'models/trained_bert_model.gz'
final_model_name = 'models/final_model.joblib'
ngrams_lst = [1,4,5]

def lambda_handler(event, context):
    input_doc = event['input_doc']
    input_doc_name = event['input_doc_name']
    source_docs = event['source_docs']
    matching_type = event['matching_type']

    if matching_type == '1-1':
        response = get_one_one_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_docs, input_doc, input_doc_name)
    else:
        response = get_one_many_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_docs, input_doc, input_doc_name)

    response_object = {}
    response_object['status_code'] = 200
    response_object['success'] = True
    response_object['body'] = response
    
    return response_object

