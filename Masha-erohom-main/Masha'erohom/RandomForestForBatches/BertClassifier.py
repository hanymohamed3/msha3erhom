
import torch
import torch.nn as nn
from transformers import BertModel
import pickle
from .Preprocessing.Preprocessing import clean_text
import numpy as np
from scipy.special import softmax
# Create the BertClassfier class
global dev 
global bertModel
global berTokenizer 
dev ,bertModel , berTokenizer = None,None,None 

class BertClassifier(nn.Module):
    """Bert Model for Classification Tasks.
    """
    def __init__(self, freeze_bert=False):
        super(BertClassifier, self).__init__()
        D_in, H, D_out = 768, 50, 8 # 8 classes
        model_path = 'UBC-NLP/MARBERTv2'
        self.bert = BertModel.from_pretrained(model_path)
        self.classifier = nn.Sequential(
            nn.Linear(D_in, H),
            nn.ReLU(),
            #nn.Dropout(0.5),
            nn.Linear(H, D_out)
        )
        if freeze_bert:
            for param in self.bert.parameters():
                param.requires_grad = False

    def forward(self, input_ids, attention_mask):
        # Feed input to BERT
        outputs = self.bert(input_ids=input_ids,
                            attention_mask=attention_mask)

        # Extract the last hidden state of the token `[CLS]` for classification task
        last_hidden_state_cls = outputs[0][:, 0, :]
        # Feed input to classifier to compute logits
        logits = self.classifier(last_hidden_state_cls)
        return logits
def load_model_and_tokenizer(model_path,tokenizer_path):
    global dev,berTokenizer,bertModel
    model = BertClassifier()
    model.load_state_dict(torch.load(model_path,map_location=dev))
    with open(tokenizer_path, 'rb') as f:
        tokenizer = pickle.load(f)
    return model,tokenizer



def predict_bert( my_input):
    global dev,berTokenizer,bertModel
    encoded_text =berTokenizer.encode_plus(
    clean_text(my_input),
    return_tensors='pt',
    )
    input_ids = encoded_text['input_ids'].to(dev)
    attention_mask = encoded_text['attention_mask'].to(dev)
    output = bertModel(input_ids, attention_mask)
    output = np.squeeze(output.detach().numpy())
    output = softmax(output)
    # if ((output[-2] >=0.5) & (output[-2] <= 0.80)):
    #     output[-2] -= 0.3
    #     output[0] +=0.3
    return output
    
    #print(f'tweet text: {my_input}')
    #print(f'Emotion  : {class_names[prediction]}')
   # print(" ")
    
def initdevice():
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f'There are {torch.cuda.device_count()} GPU(s) available.')
        print('Device name:', torch.cuda.get_device_name(0))
        return device
    else:
        print('No GPU available, using the CPU instead.')
        device = torch.device("cpu")
        return device
    
def initializeModel(model_path,tokenizer_path):
    global dev,berTokenizer,bertModel
    dev = initdevice() 
    bertModel , berTokenizer = load_model_and_tokenizer(model_path=model_path,tokenizer_path=tokenizer_path)
     
    