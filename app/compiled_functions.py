import os
os.environ['TRANSFORMERS_CACHE'] = '/tmp/.cache/huggingface/hub'

import difflib
import json
import re
from statistics import mean

import boto3
import joblib
import nltk
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textmatcher import Matcher, Text


######## CONFIGURATIONS ########

s3_bucket = 'nus-sambaash-2'
s3_training_data_filepath = 'plagiarism-detector/webis_db.csv'
sentbert_model_name = 'models/trained_bert_model.joblib'
final_model_name = 'models/final_model.joblib'
ngrams_lst = [1,4,5]


######## DIRECT MATCHING FUNCTIONS ########

def get_preprocessed_sent(input_doc):
    """
    Returns input document, split by sentences

    Args:
        input_doc (str): Input document.
    
    Returns:
        res (list[tuple]): Input document, split by sentences. Contains tuple (start_ind, end_ind, sentence)
    """
    input_doc = str(input_doc)
    input_doc = input_doc.replace('\n', '')

    input_text_lst = re.split(r' *[\.\?!][\'"\)\]]* *', input_doc)
    input_text_lst = [text for text in input_text_lst if text]

    res = []
    start_char = 1

    for s in range(len(input_text_lst)):
        res.append({'sentence': input_text_lst[s], 'start_char_index': start_char, 'end_char_index': start_char + len(input_text_lst[s])-1})
        start_char = start_char + len(input_text_lst[s])
    
    return res

def get_matching_texts(input_text_lst, source_doc, source_doc_name):
    """
    Returns list of dictionary of matching texts 
        (input_doc_text, input_doc_start, input_doc_end, source_doc_text, 
        source_doc_start, source_doc_end, source_doc_id, cosine_similarity_score) &
        the sentence indices of input documents that are flagged as direct matches.
    
    Args:
        input_text_lst (list): Input document of interest, split by sentences.
        source_doc (string): Source input document.
        source_doc_name (str): Name of source document.

    Returns:
        output_lst (list): List of dictionary of matching texts and their details.
        match_lst (list): List of dictionary of direct matching texts and their indices. 
    """
    output_lst = []
    match_lst = []
    source_doc = Text(source_doc)

    for input_sent_dict in input_text_lst:
        input_sent = input_sent_dict['sentence']
        if len(input_sent.split()) <= 3:
            continue
        try:
            input_sent = Text(input_sent)
            match = Matcher(input_sent, source_doc).match()
            if len(match) != 0:
                match_lst.append(input_sent_dict)
                output_dict = input_sent_dict.copy()
                output_dict['source_sentence'] = match[0]['source_sentence']
                output_dict['source_doc_name'] = source_doc_name
                output_dict['score'] = match[0]['score']
                output_lst.append(output_dict)
                    
        except:
            pass

    return output_lst, match_lst
        

def get_non_direct_texts(input_text_lst, match_lst):
    """
    Returns a list of dictionaries of input document's non-direct matching indices & texts.

    Args:
        input_text_lst (list): Input document, split by sentences.
        match_ind_lst (list): Sentence indices of input documents that are flagged as direct matches.

    Returns:
        nonmatch_lst (list[dict]): Input document that is not detected as direct matches, split by sentences. Contains tuple (start_ind, end_ind, sentence).
    """
    
    nonmatch_lst = []

    for i in input_text_lst:
        if i not in match_lst:
            nonmatch_lst.append(i)

    return nonmatch_lst

def modified_output_lists(direct_output_lst, para_output_lst, threshold=0.95):
    """
    Returns the modified output lists for both direct matching and paraphrasing lists, given threshold.
    Output with similarity scores > threshold in the paraphrased output list will be moved to the direct output list.

    Args:
        direct_output_lst (list): List of dictionary of direct matching texts and their details.
        para_output_lst (list): List of dictionary of paraphrased texts and their details.
        threshold (float): Threshold of similarity score to flag paraphrased texts as direct matches.

    Returns:
        new_direct_lst (list): Modified list of dictionary of direct matching texts and their details.
        new_para_lst (list): Modified list of dictionary of paraphrased texts and their details.
    """
    filter_para_lst = []
    new_para_lst = []

    for dict in para_output_lst:
        if dict['score'] >= threshold:
            filter_para_lst.append(dict)
        else:
            new_para_lst.append(dict)

    new_direct_lst = direct_output_lst + filter_para_lst 

    return new_direct_lst, new_para_lst

def get_avg_score(input_text_lst, output_lst):
    """
    Returns the average of cosine similarity scores over number of sentences in input document.

    Args:
        input_text_lst (list): Input document, split by sentences.
        output_lst (list):  List of dictionary of matching texts and their details.

    Returns:
        avg_score (float): Average cosine similarity scores over number of sentences in input document.
    """
    input_doc_len = len(input_text_lst)
    total_score = 0
    for score in output_lst:
        total_score += score['score']
    avg_score = total_score / input_doc_len

    return avg_score


######## PARAPHRASED MATCHING FUNCTIONS ########

def load_model(model_name):
    ""
    model = joblib.load(model_name)
    return model

def get_paraphrase_predictions(model, nonmatch_lst, source_doc, source_doc_name, threshold):
    """
    Returns a list of json containing paraphrased sentences' details, predicted from trained Sentence Transformer model.
    
    Args: 
        model (SentenceTransformer): Sentence Transformer model.
        nonmatch_lst (list[str]): List of sentences not detected as direct matches. 
        source_doc (str): Source document.
        source_doc_name (str): Name of source document.
        threshold (float): Threshold of similarity score to flag sentence as paraphrased.
            
    Returns:
        res_list (list[dict]): List of json containing paraphrased sentence details.
        example:
        [
            {
              "sentence": "\"enraged at their disappointment, Irish soldiers carved Scandinavian Stern in pieces, and is still coveted secret unrevealed.",
              "start_char_index": 2179,
              "end_char_index": 2303,
              "source_sentence": "Enraged\nat their disappointment, the Irish soldiers hewed the stern northman in pieces, and the coveted\nsecret is still unrevealed.",
              "score": 0.8140799403190613
            }
        ]
    """
    res_list = []
    try:
        source_sent = re.split(r' *[\.\?!][\'"\)\]]* *', source_doc)
        source_sent = [text for text in source_sent if text]

        for input_sent_dict in nonmatch_lst:
            input_sent = input_sent_dict['sentence']
            if len(input_sent.split()) <= 3:
                continue

            source_embeddings = model.encode(source_sent)
            input_embeddings = model.encode(input_sent)

            res = cosine_similarity(
                    [input_embeddings],
                    source_embeddings
                )

            score = float(max(res[0]))

            if score > threshold:
                temp = input_sent_dict
                temp['source_sentence'] = source_sent[res[0].argmax()]
                temp['source_doc_name'] = source_doc_name
                temp['score'] = score
                res_list.append(temp)
    except:
        pass
                
    return res_list


######## FEATURE GENERATION FUNCTIONS ########

def get_vocab_counts(input_doc, source_doc, n):
    '''
    Using CountVectorizer, create vocab based on both texts.
    Count number of occurence of each ngram
    '''
    counts_ngram = CountVectorizer(analyzer='word', ngram_range=(n, n))
    vocab = counts_ngram.fit([input_doc, source_doc]).vocabulary_
    counts = counts_ngram.fit_transform([input_doc, source_doc])
    
    return vocab, counts.toarray()

# calculate ngram containment for each text/original file
def calc_containment(input_doc, source_doc, n):
    '''
    calculates the containment between a given text and its original text
    This creates a count of ngrams (of size n) then calculates the containment by finding the ngram count for a text file
    and its associated original tezt -> then calculates the normalised intersection
    '''
    # create vocab and count occurence of each ngram
    vocab, ngram_counts = get_vocab_counts(input_doc, source_doc, n)
    # calc containment
    intersection_list = np.amin(ngram_counts, axis = 0)
    intersection = np.sum(intersection_list)
    count_ngram = np.sum(ngram_counts[0])
    
    return intersection / count_ngram

def get_containment_scores(input_doc, source_doc, ngrams_lst):
    containment_scores = {}
    
    for ngram in ngrams_lst:
        containment = calc_containment(input_doc, source_doc, ngram)
        key_name = f"c_{ngram}"
        containment_scores[key_name] = containment
    
    return containment_scores

def get_n_avg_containment_scores(containment_scores_lst, ngrams_lst):
    """
    Get average containment scores from all the containment scores generated across all the source_documents.

    Args:
        containment_scores_lst (list[dict]): A list of dictionaries containing each source_document & input_document pair's containment scores.
        ngrams_lst (lst): List of selected n_grams used to generate containment scores.

    Returns:
        avg_containment_scores (dict): A dictionary of all average containment_scores across all source_documents.
    """
    avg_containment_scores = {}

    for ngram in ngrams_lst: 
        key_name = f"c_{ngram}"
        avg_containment_scores[key_name]= mean([containment.get(key_name) for containment in containment_scores_lst])

    return avg_containment_scores


def get_lcm_score(input_doc, source_doc):
    max_len = max(len(input_doc), len(source_doc))
    matcher = difflib.SequenceMatcher(None, input_doc, source_doc)
    
    # calculate the ratio of the longest common subsequence and the length of the longer text
    lcs_ratio = matcher.find_longest_match(0, len(input_doc), 0, len(source_doc)).size / max_len
    
    return lcs_ratio


######## FINAL MODEL LOADING & PREDICTION FUNCTIONS ########

def get_feature_dict(containment_scores, lcm_score, direct_avg_score, paraphrase_avg_score):
    """
    Get a DataFrame of all features to be parsed to the trained model.

    Args:
        containment_scores (dict): A dictionary containing N n-grams containment score.
        lcm_score (float): Ratio of the longest common subsequence and the length of the longer text.
        direct_avg_score (float): Average similarity score of detected direct matching texts across the input document.
        paraphrase_avg_score (float): Average similarity score of detected paraphrased texts across the input document.

    Returns:
        feature_df (pd.DataFrame): Dataframe of all features to be parsed to the trained model (containment scores, LCM score, average cosine similarity scores from direct matching & paraphrased texts).
    """
    containment_scores['lcs_word'] = lcm_score
    containment_scores['para_detect_score'] = direct_avg_score
    containment_scores['direct_detect_score'] = paraphrase_avg_score
    feature_df = pd.DataFrame(containment_scores, index=[0])
    
    return feature_df

def get_flag_score_prediction(final_model_name, feature_df):
    """
    Returns the flag and probability predictions from the trained final model. 

    Args:
        final_model_name (final): Trained final model.
        feature_df (pd.DataFrame): Dataframe of all features to be parsed to the trained final model.

    Returns:
        plagiarism_flag (boolean): 1 means the document is plagiarised, vice-versa.
        plagiarism_scoreability (float): Probability of the document being flagged as plagiarised.
    """
    final_model = load_model(final_model_name)

    plagiarism_flag = final_model.predict(feature_df)[0]
    plagiarism_score = final_model.predict_proba(feature_df)[:,1][0]
    
    return plagiarism_flag, plagiarism_score


######## GENERIC MATCHING OUTPUT GENERATION FUNCTIONS ########

def one_one_matching_texts(sentbert_model_name, ngrams_lst, source_doc, source_doc_name, input_doc):
    """
    One-to-one matching function - given 2 documents, compare and return the plagiarised flag, score and plagiarised texts.

    Args:
        sentbert_model_name (str): Filepath of trained Sentence Transformer model.
        ngrams_lst (lst): List of selected n_grams used to generate containment scores.
        source_doc (str): Source document.
        source_doc_name (str): Name of source document.
        input_doc (str): Input document.

    Returns:
        plagiarised_text (list): Concatenation of direct matching and paraphrasing texts, sorted by starting character index. 
        direct_avg_score (float): Average direct matching cosine similarity score over number of sentences in input document.
        paraphrase_avg_score (float): Average paraphrase cosine similarity score over number of sentences in input document.
        containment_scores (dict): Containment scores for each ngram between the source and input document.
        lcm_score (flat): Longest common subsequence score between the source and input document.
    """
    input_text_lst = get_preprocessed_sent(input_doc)
    direct_output, match_lst = get_matching_texts(input_text_lst, source_doc, source_doc_name)
    
    nonmatch_lst = get_non_direct_texts(input_text_lst, match_lst)
    sentence_trans_model = load_model(sentbert_model_name)
    paraphrase_output = get_paraphrase_predictions(sentence_trans_model, nonmatch_lst, source_doc, source_doc_name, 0.7)

    plagiarised_text = direct_output + paraphrase_output
    plagiarised_text = sorted(plagiarised_text, key=lambda d: d['start_char_index'])

    new_direct_output, new_paraphrase_output = modified_output_lists(direct_output, paraphrase_output, 0.95)
    
    direct_avg_score = get_avg_score(input_text_lst, new_direct_output)
    paraphrase_avg_score = get_avg_score(input_text_lst, new_paraphrase_output)
    
    containment_scores = get_containment_scores(input_doc, source_doc, ngrams_lst)
    lcm_score = get_lcm_score(input_doc, source_doc)

    return plagiarised_text, direct_avg_score, paraphrase_avg_score, containment_scores, lcm_score

def one_one_matching_flag_score(sentbert_model_name, final_model_name, ngrams_lst, source_doc, source_doc_name, input_doc, input_doc_name):
    """
    Generates the plagiarism flag and score for a input and source document pair.

    Args:  
        sentbert_model_name (str): Filepath of trained Sentence Transformer model.
        final_model_name (str): Filepath of trained final model.
        ngrams_lst (lst): List of selected n_grams used to generate containment scores.
        source_doc (str): Source document.
        source_doc_name (str): Name of source document.
        input_doc (str): Input document.
        input_doc_name (str): Name of input document.

    Returns:
        output_dict (dict): Dictionary containing comparison results (name of input document, plagiarised flag, score and texts).
    """

    plagiarised_text, direct_avg_score, paraphrase_avg_score, containment_scores, lcm_score = one_one_matching_texts(sentbert_model_name, ngrams_lst, source_doc, source_doc_name, input_doc)

    feature_df = get_feature_dict(containment_scores, lcm_score, direct_avg_score, paraphrase_avg_score)
    
    plagiarism_flag, plagiarism_score = get_flag_score_prediction(final_model_name, feature_df)
    
    output_dict = {'input_doc_name': input_doc_name,
                   'plagiarism_flag': plagiarism_flag, 
                   'plagiarism_score': plagiarism_score,
                   'plagiarised_text': plagiarised_text}

    return output_dict


######## 1-1 MATCHING FINAL OUTPUT GENERATION FUNCTIONS ########

def get_one_one_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_docs, input_doc, input_doc_name):
    """
    One-to-one matching function - given 2 documents, compare and return the plagiarised flag, score and plagiarised texts.
    Args:
        sentbert_model_name (str): Filepath of trained Sentence Transformer model.
        final_model_name (str): Filepath of trained final model.
        ngrams_lst (lst): List of selected n_grams used to generate containment scores.
        source_docs (list[dict]): List of dictionaries containing source documents & source document name. E.g. [{'source_doc_name': test1, 'source_doc': teststr}]
        input_doc (str): Input document.
        input_doc_name (str): Name of input document.
    
    Returns:
        output_lst (list[dict]): List of dictionaries containing all comparison results (name of input document, plagiarised flag, score and texts).
    """
    output_lst = []
    for i in source_docs:

        source_doc = i['source_doc']
        source_doc_name = i['source_doc_name']

        temp_dict = one_one_matching_flag_score(sentbert_model_name, final_model_name, ngrams_lst, source_doc, source_doc_name, input_doc, input_doc_name)
        output_lst.append(temp_dict)

        add_input_data(source_docs, input_doc, input_doc_name, s3_bucket, s3_training_data_filepath)

    return output_lst


######## 1-MANY MATCHING FINAL OUTPUT GENERATION FUNCTIONS ########

def get_one_many_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_docs, input_doc, input_doc_name):
    """
    One-to-many matching function - given 1 input document & >1 source documents, compare and return the plagiarised flag, score and plagiarised texts.
    Args:
        sentbert_model_name (str): Filepath of trained Sentence Transformer model.
        final_model_name (str): Filepath of trained final model.
        ngrams_lst (lst): List of selected n_grams used to generate containment scores.
        source_docs (list[dict]): List of dictionaries containing source documents & source document name. E.g. [{'source_doc_name': test1, 'source_doc': teststr}]
        input_doc (str): Input document.
        input_doc_name (str): Name of input document.
    
    Returns:
        output_dict (dict): Dictionary containing all comparison results, averaged across all source_documents (name of input document, plagiarised flag, score and texts).
    """

    plagiarised_text_lst = []
    direct_avg_score_lst = []
    paraphrase_avg_score_lst = []
    containment_scores_lst = []
    lcm_score_lst = []

    for i in source_docs:
        plagiarised_text, direct_avg_score, paraphrase_avg_score, containment_scores, lcm_score = one_one_matching_texts(sentbert_model_name, ngrams_lst, i['source_doc'], i['source_doc_name'], input_doc)
                
        plagiarised_text_lst = plagiarised_text_lst + plagiarised_text
        direct_avg_score_lst.append(direct_avg_score)
        paraphrase_avg_score_lst.append(paraphrase_avg_score)
        containment_scores_lst.append(containment_scores)
        lcm_score_lst.append(lcm_score)

    avg_containment_scores = get_n_avg_containment_scores(containment_scores_lst, ngrams_lst)

    feature_df = get_feature_dict(avg_containment_scores, mean(lcm_score_lst), mean(direct_avg_score_lst), mean(paraphrase_avg_score_lst))

    plagiarism_flag, plagiarism_score = get_flag_score_prediction(final_model_name, feature_df)

    add_input_data(source_docs, input_doc, input_doc_name, s3_bucket, s3_training_data_filepath)

    output_dict = {'input_doc_name': input_doc_name,
                    'plagiarism_flag': plagiarism_flag, 
                    'plagiarism_score': plagiarism_score,
                    'plagiarised_text': plagiarised_text_lst}
    
    return output_dict

######## ADD NEW INPUT TO TRAINING DATAFILE ########

def read_s3_df(s3_bucket, s3_filepath):
    """
    Returns DataFrame of CSV file downloaded from S3 bucket.

    Args:
        s3_bucket (str): Name of S3 bucket.
        s3_filepath (str): Filepath of CSV file in S3.

    Returns:
        df (pd.DataFrame): Dataframe of CSV file downloaded.
    """
    data_location = 's3://{}/{}'.format(s3_bucket, s3_filepath)
    df = pd.read_csv(data_location, index_col=[0])
    
    return df

def upload_to_s3(local_file, s3_bucket, s3_filepath):
    """
    Uploads file back to S3 bucket.

    Args:
        local_file (str): Local filepath of file.
        s3_bucket (str): Name of S3 bucket.
        s3_filepath (str): Filepath of file in S3.

    Returns:
        s3_url (str): S3 URL of file uploaded.
    """
    s3_client = boto3.client("s3")
    s3_url = s3_client.upload_file(local_file, s3_bucket, s3_filepath)

    return s3_url

def add_input_data(source_docs, input_doc, input_doc_name, s3_bucket, s3_training_data_filepath):
    """
    Adds the new input and source documents back to training data file in S3 bucket.

    Args:
        source_docs (list[dict]): A list of dictionaries containing the input and source documents.
        input_doc (str): Input document.
        input_doc_name (str): Name of input document.
        s3_bucket (str): Name of S3 bucket.
        s3_filepath (str): Filepath of file in S3.
    """
    training_df = read_s3_df(s3_bucket, s3_training_data_filepath)
    
    for dict in source_docs:
        data = {
            "file_num": dict['source_doc_name'],
            "text": dict['source_doc']
        }
        training_df = training_df.append(data, ignore_index=True) 

    data = {
        "file_num": input_doc_name,
        "text": input_doc
    }
    training_df = training_df.append(data, ignore_index=True) 
    
    training_df.to_csv('/tmp/webis_db.csv', index=False)
    upload_to_s3('/tmp/webis_db.csv', s3_bucket, s3_training_data_filepath)

    return None


