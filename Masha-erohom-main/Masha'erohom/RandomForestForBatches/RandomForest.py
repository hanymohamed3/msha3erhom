from .Preprocessing.Preprocessing import clean_text
from .BertClassifier import *
from .BiLSTM_BiGRU import *
from joblib import load 
import numpy as np
from threading import Lock


global randomForest 
randomForest = None

global lock 
lock = Lock()

CLASSNAMES = ['none', 'anger', 'joy', 'sadness', 'love', 'sympathy', 'surprise', 'fear']


def initialize_random_forest(randomforestPath,bertPath,bertokenizerPath,lstmPath,gruPath,lstmgrutokenizerPath):
    global randomForest,lock
    lock.acquire()
    if ((randomForest != None)):
        lock.release()
        return
    else:
        print("######################### INITIALIZING ALL THE MODELS #########################")
        randomForest  = load(randomforestPath)
        initializeModel(bertPath,bertokenizerPath)
        initModels(lstmPath,gruPath,lstmgrutokenizerPath)
    lock.release()
    
def get_sentiments(text):
    global randomForest
    
    marbert_predictions = [predict_bert(t) for t in text]
    lstm_predictions = predict_lstm(text)
    gru_predictions = predict_gru(text)
    rf_input = np.concatenate([marbert_predictions,lstm_predictions,gru_predictions],axis=1)
    rf_prediction = randomForest.predict(rf_input)
    for i in range(len(rf_prediction)):
        if rf_prediction[i] == 6:
            marbertMax = np.argmax(marbert_predictions[i])
            if marbertMax != 6:
                # DEBUGGING PRINT
                #print('eliminated 2 weak models surprise class')
                rf_prediction[i] = marbertMax
            else:
                for soft in [marbert_predictions[i],lstm_predictions[i],gru_predictions[i]]:
                    soft[0] +=0.5
                    soft[1:] = max((soft[6]- 0.5),0.02)
                rf_prediction[i] = randomForest.predict([rf_input[i]])[0]
                if rf_prediction[i] != 6:
                    rf_prediction[i] = 0
    
    # DEBUGGING PRINT
    
    # print(f"""    
    #       {text}:
          
    #                     none anger joy sadness love sympathy surprise fear 
    #       marbert_soft = {list(marbert_predictions)} 
    #       lstm_soft = {list(lstm_predictions)} 
    #       gru_soft = {list(gru_predictions)}
    #       classification = {CLASSNAMES[rf_prediction[0]]}
          
    #       """
    #       )
    # for i in range(len(rf_prediction)):
    #     print(f"""
    #           text : {text[i]}
    #           Marbert : {CLASSNAMES[np.argmax(marbert_predictions[i])]}
    #           lstm : {CLASSNAMES[np.argmax(lstm_predictions[i])]}
    #           gru : {CLASSNAMES[np.argmax(gru_predictions[i])]}
    #           random forest : {CLASSNAMES[rf_prediction[i]]}
    #           """)
    rf_prediction = [CLASSNAMES[pred] for pred in rf_prediction]
    
    return rf_prediction


def avoid_classes_overfitting(softmax_output):
    if (np.argmax(softmax_output) == -2 ): 
        next_probable_class = np.argmax(np.delete(softmax[-2]))
        if (softmax_output[-2] - softmax_output[next_probable_class]) <= 0.15 : 
            print(f""" 
                  found a surprise overfit with {softmax_output[-2]} probability and the second one is {CLASSNAMES[next_probable_class]} with {softmax_output[next_probable_class]}
                  """)
            softmax_output[-2] -= 0.15
            softmax_output[next_probable_class] += 0.15
            
    return softmax_output

def normalize_regularity(array,index_to_increase):
    if index_to_increase == np.argmax(array) :
        return array
    for i in range(8):
        if array[i] >=0.4:
            if array[i]>= 0.65 :
                array[i] -= 0.55
            else:
                array[i] -= 0.3
        else:
            array[i] = max((array[i]-0.1),0.02)
    array[index_to_increase] += 0.4
    return array