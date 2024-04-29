from joblib import load
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import tokenizer_from_json
from keras.models import load_model
import json
import numpy as np 
from .Preprocessing.Preprocessing import clean_text


global biLstm_model
global bigru_model
global lstmgrutokenzier
 
biLstm_model , bigru_model ,lstmgrutokenzier = None,None,None 

LSTM_GRU_MAP = [4,0,2,5,3,7,6,1]

def tokenize_input(texts):
    global lstmgrutokenzier
    text = [clean_text(text) for text in texts]
    text = lstmgrutokenzier.texts_to_sequences(text)
    text = pad_sequences(text, padding='post', maxlen=300)
    return text 

def predict_lstm(text):
    global biLstm_model
    tokenized = tokenize_input(text)
    predictions = biLstm_model.predict(tokenized) 
    # predictions = np.squeeze(predictions)
    predictions[:] = predictions[:,LSTM_GRU_MAP] 
    # if ((predictions[-2] >=0.5) & (predictions[-2] <= 0.80)):
    #     predictions[-2] -= 0.25
    #     predictions[0] +=0.25
    
    return predictions


def predict_gru(text):
    global bigru_model
    tokenized = tokenize_input(text)
    predictions = bigru_model.predict(tokenized) 
    predictions[:] = predictions[:,LSTM_GRU_MAP] 
    # if ((predictions[-2] >=0.5) & (predictions[-2] <= 0.80)):
    #     predictions[-2] -= 0.25
    #     predictions[0] +=0.25
   
    return predictions


def initModels(lstm_path,gru_path,tokenizer_path):
    global biLstm_model , bigru_model , lstmgrutokenzier
    
    biLstm_model = load_model(lstm_path)
    bigru_model = load_model(gru_path)
    with open(tokenizer_path, 'r') as f:
        tokenizer_config = json.load(f)
    tokenizer_json = json.dumps(tokenizer_config)
    lstmgrutokenzier = tokenizer_from_json(tokenizer_json)