import os

os.environ['TRANSFORMERS_CACHE'] = '/tmp/.cache/huggingface/hub'

import difflib
import io
import re
from io import BytesIO
from statistics import mean

import boto3
import joblib
import numpy as np
import pandas as pd
from pypdf import PdfReader
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textmatcher import Matcher, Text

######## CONFIGURATIONS ########

s3_bucket = 'nus-sambaash'
s3_pdf_filepath = 'plagiarism-detector/data/pdfs'
s3_webis_data_filepath = 'plagiarism-detector/data/webis_db.csv'
s3_training_data_filepath = 'plagiarism-detector/data/train.csv'
s3_output_data_filepath = 'plagiarism-detector/data/output.csv'
sentbert_model_name = 'plagiarism-detector/models/trained_bert_model.joblib'
final_model_name = 'plagiarism-detector/models/final_model.joblib'
ngrams_lst = [1,4,5]


######## PREPROCESSING FUNCTIONS ########

def read_s3_df(s3_bucket, s3_filepath):
    """
    Returns DataFrame of CSV file downloaded from S3 bucket.

    Args:
        s3_bucket (str): Name of S3 bucket.
        s3_filepath (str): Filepath of CSV file in S3.

    Returns:
        df (pd.DataFrame): Dataframe of CSV file downloaded.
    """
    s3_client = boto3.client('s3')
    obj = s3_client.get_object(Bucket=s3_bucket, Key= s3_filepath)
    df = pd.read_csv(obj['Body'])
    
    return df

def read_s3_pdf(s3_bucket, filename):
    """
    Returns string of parsed text from a PDF file in S3 bucket.

    Args:
        s3_bucket (str): Name of S3 bucket.
        filename (str): Filename of PDF file in S3.
    
    Returns:
        text (str): String of parsed text from PDF file.
    """
    s3_client = boto3.client('s3')
    filepath = os.path.join(s3_pdf_filepath, filename)
    s3_obj= s3_client.get_object(Bucket=s3_bucket, Key=filepath)
    reader = PdfReader(BytesIO(s3_obj['Body'].read()))
    text = ""

    for page in reader.pages:
        text += page.extract_text().replace('\n', ' ')

    return text


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
                output_dict['source_sentence'] = match[0]['sentence']
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

def load_s3_model(s3_bucket, s3_filepath):
    """
    Load trained model from S3.

    Args:
        s3_bucket (str): Name of S3 bucket.
        s3_filepath (str): Filepath of trained model in S3.

    Returns:
        model (SentenceTransformers or LogisticRegression): Trained model.
    """
    s3_client = boto3.client('s3')
    obj = s3_client.get_object(Bucket=s3_bucket, Key= s3_filepath)
    model = joblib.load(io.BytesIO(obj['Body'].read()))
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
    """
    Using CountVectorizer, create vocab based on both texts.
    Count number of occurence of each ngram.

    Args:
        input_doc (str): Input document.
        source_doc (str): Source document.
        n (int): Number of n-gram calculated.

    Returns:
        vocab (dict) : Vocabulary (i.e. unique tokens in the 2 doc and their corresponding indices in the sparse matrix).
        counts.toarray() (arr) : Array of integers where each row represents the token counts for a document.
    """

    counts_ngram = CountVectorizer(analyzer='word', ngram_range=(n, n))
    vocab = counts_ngram.fit([input_doc, source_doc]).vocabulary_
    counts = counts_ngram.fit_transform([input_doc, source_doc])
    
    return vocab, counts.toarray()

# calculate ngram containment for each text/original file
def calc_containment(input_doc, source_doc, n):
    """
    Calculates the containment between a given text and its original text.
    This creates a count of ngrams (of size n) then calculates the containment by finding the ngram count for a text file and its associated original text -> then calculates the normalised intersection.

    Args:
        input_doc (str): Input document.
        source_doc (str): Source document.
        n (int): Number of n-gram calculated.

    Returns:
        intersection / count_ngram (float): Containment similarity score between the 2 documents.
    """
    # create vocab and count occurence of each ngram
    vocab, ngram_counts = get_vocab_counts(input_doc, source_doc, n)
    # calc containment
    intersection_list = np.amin(ngram_counts, axis = 0)
    intersection = np.sum(intersection_list)
    count_ngram = np.sum(ngram_counts[0])
    
    return intersection / count_ngram

def get_containment_scores(input_doc, source_doc, ngrams_lst):
    """
    Generates containment scores for all n-values in ngrams_lst for each input_doc.

    Args:
        input_doc (str): Input document.
        source_doc (str): Source document.
        ngrams_lst (list[int]): List of n integers of n-gram containment values to generate.

    Returns:
        containment_scores (dict): Key represents current n-gram, values are containment score for that input_doc.
    """
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
    """
    Calculates the ratio of the longest common subsequence 
    and the length of the longer text

    Args:
        input_doc (str): Input document.
        source_doc (str): Source document.

    Returns:
        lcs_ratio (float): LCS score for input_doc and source_docs.
    """
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
    final_model = load_s3_model(s3_bucket, final_model_name)

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
    sentence_trans_model = load_s3_model(s3_bucket, sentbert_model_name)
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

    #if no plagiarised text, set flag=0
    if len(plagiarised_text) == 0:
        plagiarism_flag = 0
    
    output_dict = {'input_doc_name': input_doc_name,
                   'plagiarism_flag': plagiarism_flag, 
                   'plagiarism_score': plagiarism_score,
                   'plagiarised_text': plagiarised_text}

    return output_dict


######## 1-1 MATCHING FINAL OUTPUT GENERATION FUNCTIONS ########

def get_one_one_matching_output(sentbert_model_name, final_model_name, ngrams_lst, source_doc_name, input_doc_name):
    """
    One-to-one matching function - given 2 documents, compare and return the plagiarised flag, score and plagiarised texts.
    Args:
        sentbert_model_name (str): Filepath of trained Sentence Transformer model.
        final_model_name (str): Filepath of trained final model.
        ngrams_lst (lst): List of selected n_grams used to generate containment scores.
        source_doc_name (str): Name of source document in S3.
        input_doc_name (str): Name of input document in S3.
    
    Returns:
        res (dict): Dictionary containing all comparison results (name of input document, plagiarised flag, score and texts).
    """
    input_doc = read_s3_pdf(s3_bucket, input_doc_name)
    source_doc = read_s3_pdf(s3_bucket, source_doc_name)

    res = one_one_matching_flag_score(sentbert_model_name, final_model_name, ngrams_lst, source_doc, source_doc_name, input_doc, input_doc_name)

    add_input_training_data(source_doc_name, source_doc, input_doc, s3_bucket, s3_training_data_filepath)

    return res


######## 1-MANY MATCHING FINAL OUTPUT GENERATION FUNCTIONS ########

def get_one_many_matching_output(sentbert_model_name, final_model_name, ngrams_lst, input_doc_name):
    """
    One-to-many matching function - given 1 input document, compare with the database of documents in S3 and return the plagiarised flag, score and plagiarised texts.
    Args:
        sentbert_model_name (str): Filepath of trained Sentence Transformer model.
        final_model_name (str): Filepath of trained final model.
        ngrams_lst (lst): List of selected n_grams used to generate containment scores.
        source_docs (list[dict]): List of dictionaries containing source documents & source document name. E.g. [{'source_doc_name': test1, 'source_doc': teststr}]
        input_doc_name (str): Name of input document.
    
    Returns:
        output_dict (dict): Dictionary containing all comparison results, averaged across all source_documents (name of input document, plagiarised flag, score and texts).
    """
    plagiarised_text_lst = []
    direct_avg_score_lst = []
    paraphrase_avg_score_lst = []
    containment_scores_lst = []
    lcm_score_lst = []

    input_doc = read_s3_pdf(s3_bucket, input_doc_name)
    webis_df = read_s3_df(s3_bucket, s3_webis_data_filepath).head(2) # This is the database of documents to check through. We filtered only the top 2 rows for testing purposes.

    for index, row in webis_df.iterrows():
        if row['file_num'] == input_doc_name:
            continue
        plagiarised_text, direct_avg_score, paraphrase_avg_score, containment_scores, lcm_score = one_one_matching_texts(sentbert_model_name, ngrams_lst, row['text'], row['file_num'], input_doc)
                
        plagiarised_text_lst = plagiarised_text_lst + plagiarised_text
        direct_avg_score_lst.append(direct_avg_score)
        paraphrase_avg_score_lst.append(paraphrase_avg_score)
        containment_scores_lst.append(containment_scores)
        lcm_score_lst.append(lcm_score)

    avg_containment_scores = get_n_avg_containment_scores(containment_scores_lst, ngrams_lst)

    feature_df = get_feature_dict(avg_containment_scores, mean(lcm_score_lst), mean(direct_avg_score_lst), mean(paraphrase_avg_score_lst))

    plagiarism_flag, plagiarism_score = get_flag_score_prediction(final_model_name, feature_df)

    output_dict = {'input_doc_name': input_doc_name,
                    'plagiarism_flag': plagiarism_flag, 
                    'plagiarism_score': plagiarism_score,
                    'plagiarised_text': plagiarised_text_lst}
    
    return output_dict

######## ADD INPUT TO S3 ########

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

def add_input_training_data(source_doc_name, source_doc, input_doc, s3_bucket, s3_training_data_filepath):
    """
    Adds the new input and source documents back to training data file in S3 bucket.

    Args:
        source_doc_name (str): Name of source document.
        source_doc (str): Source document.
        input_doc (str): Input document.
        input_doc_name (str): Name of input document.
        s3_bucket (str): Name of S3 bucket.
        s3_training_data_filepath (str): Filepath of file in S3.
    """
    training_df = read_s3_df(s3_bucket, s3_training_data_filepath)

    data = pd.DataFrame({
        "file_num": [source_doc_name],
        "text_og": [source_doc],
        "text_para": [input_doc]
    })
    training_df = training_df.append(data, ignore_index=True) 
    
    training_df.to_csv('/tmp/train.csv', index=False)
    upload_to_s3('/tmp/train.csv', s3_bucket, s3_training_data_filepath)

    return None

def add_input_data(user_id, input_doc_name, input_doc, s3_bucket, s3_webis_data_filepath):
    """
    Adds the new input and source documents back to existing database for documents to be checked against in S3 bucket.

    Args:
        input_doc_name (str): Name of input document.
        input_doc (str): Input document.
        s3_bucket (str): Name of S3 bucket.
        s3_webis_data_filepath (str): Filepath of file in S3.
    """
    webis_df = read_s3_df(s3_bucket, s3_webis_data_filepath)

    data = pd.DataFrame({
        "user_id": [user_id],
        "file_num": [input_doc_name],
        "text": [input_doc]
    })
    webis_df = pd.concat([webis_df, data], ignore_index=True) 
    
    webis_df.to_csv('/tmp/webis_db.csv', index=False)
    upload_to_s3('/tmp/webis_db.csv', s3_bucket, s3_webis_data_filepath)

    return None

def add_output_data(user_id, input_doc_name, response, matching_type, s3_bucket, s3_output_data_filepath, source_doc_name):
    """
    Adds the new input, source documents and API response to output data file in S3 bucket.

    Args:
        created_at (datetime): Datetime when data is inserted.
        user_id (str): user ID.
        nput_doc (str): Input document.
        input_doc_name (str): Name of input document.
        response (dict/ list[dict)]: API response body.
        s3_bucket (str): Name of S3 bucket.
        s3_output_data_filepath (str): Filepath of file in S3.
        source_docs (list[dict]): List of dictionaries containing source documents & source document name. E.g. [{'source_doc_name': test1, 'source_doc': teststr}]
    """
    output_df = read_s3_df(s3_bucket, s3_output_data_filepath)

    data = {
            "created_at": pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S"),
            "matching_type": matching_type,
            "user_id": user_id,
            "source_doc_name": source_doc_name,
            "input_doc_name": input_doc_name,
            "plagiarism_flag": response["plagiarism_flag"],
            "plagiarism_score": response["plagiarism_score"],
            "plagiarised_text": response["plagiarised_text"]
        }
    output_df = output_df.append(data, ignore_index=True) 
    
    output_df.to_csv('/tmp/output.csv', index=False)
    upload_to_s3('/tmp/output.csv', s3_bucket, s3_output_data_filepath)

    return None