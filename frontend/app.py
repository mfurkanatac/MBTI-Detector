from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

# Load the saved BERT model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=16)
model.load_state_dict(torch.load('final_model.pt'))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Load BERT tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

label_mapping = {
    0: "ISTJ",
    1: "ISFJ",
    2: "INFJ",
    3: "INTJ",
    4: "ISTP",
    5: "ISFP",
    6: "INFP",
    7: "INTP",
    8: "ESTP",
    9: "ESFP",
    10: "ENFP",
    11: "ENTP",
    12: "ESTJ",
    13: "ESFJ",
    14: "ENFJ",
    15: "ENTJ",
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handleMessage(message):
    colors = ['#00ff00', '#ff0000', '#0000ff', '#ffff00', '#ff00ff']

    

    if len(message) > 600:
        emit('message', 'Error: Input exceeded the maximum limit of 600 characters')
    else:
        with torch.no_grad():
            inputs = tokenizer(message, return_tensors='pt').to(device)
            outputs = model(**inputs)

        logits = outputs.logits.detach().cpu().numpy()
        # Compute softmax over the logits
        probabilities = torch.nn.functional.softmax(torch.from_numpy(logits[0]), dim=0).numpy()
        # Get the indices of the top 5 predictions
        top5_pred_indices = probabilities.argsort()[-5:][::-1]
        # Get the top 5 predictions and their probabilities
        top5_predictions = [(label_mapping[i], probabilities[i]) for i in top5_pred_indices]
        
        emit('message', '<br>'.join([f"<span style='color:{colors[i]}'>{i+1}. {pred}: {prob:.2f}%</span>" for i, (pred, prob) in enumerate(top5_predictions)]))

if __name__ == '__main__':
    socketio.run(app)
