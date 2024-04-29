from flask import Flask, Blueprint, render_template, request, make_response, send_from_directory, redirect, url_for , jsonify,copy_current_request_context
from flask_login import login_required, current_user
from .models import File
from werkzeug.utils import secure_filename
from datetime import datetime
from . import db
from flask import session
from RandomForestForBatches.RandomForest import get_sentiments
import pandas as pd
import os
import json
from .scraper import get_twitterSentiments
from RandomForestForBatches.RandomForest import initialize_random_forest
from flask import current_app
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore,Lock
from flask import send_file
import io

global user_semaphore
global lock 
user_semaphore = Semaphore(1)
lock = Lock()

views = Blueprint('views', __name__)
ALLOWED_EXTENSIONS = {'csv'}
MODELS_DIR = "RandomForestForBatches/ModelsFiles/"
global dfs
dfs = dict()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@views.route('/', methods=['GET','POST'])
@login_required
def home():
    lock.acquire()
    if current_user.id in dfs.keys():
        del dfs[current_user.id]
    lock.release()
    if request.method=='POST':
        # Check if the file is uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                Rfile = pd.read_csv(file)
                if 'text' in Rfile.columns:
                    df_json = Rfile.to_json(orient='records')
                    return render_template('Loading.html',dataframe = df_json, filename = file.filename)
                else:
                    return "The uploaded file does not contain a 'text' column."
            else:
                return "The uploaded file is not a CSV file."
        # Check if the keyword is submitted
        elif 'keyWord' in request.form:
            keyword = request.form['keyWord']
            matchType = request.form.get('type')
            return render_template('Loading.html',keyword = keyword,matchType = matchType)
        else:
            return "No file or keyword submitted."
    else:
        return render_template("home.html", user=current_user)

@login_required
@views.route('/download/<filename>',methods=['GET'])
def download(filename):
    return send_from_directory("C:\\My Projects\\Masha'erohom\\predictedData", filename, as_attachment=True)

@login_required
@views.route('/chart/<filename>', methods=['GET'])
def chart(filename):
    file_path = os.path.join('predictedData', filename)
    df = pd.read_csv(file_path)

    joy_count = (df['prediction'] == 'joy').sum()
    anger_count = (df['prediction'] == 'anger').sum()
    sadness_count = (df['prediction'] == 'sadness').sum()
    love_count = (df['prediction'] == 'love').sum()
    sympathy_count = (df['prediction'] == 'sympathy').sum()
    surprise_count = (df['prediction'] == 'surprise').sum()
    fear_count = (df['prediction'] == 'fear').sum()
    none_count = (df['prediction'] == 'none').sum()

    categories = ['joy', 'anger', 'sadness', 'love', 'sympathy', 'surprise', 'fear', 'none']
    counts = [joy_count, anger_count, sadness_count, love_count, sympathy_count, surprise_count, fear_count, none_count]
    counts = [int(count) for count in counts]
    
    categories_json = json.dumps(categories)
    counts_json = json.dumps(counts)
    return render_template('Chart.html', categories=categories_json, counts=counts_json, user=current_user, filename=filename)

@login_required
@views.route('/chart2', methods=['GET','POST'])
def ChartsWithTwitter():
    if request.method=='POST' : 
        dataframe_in_json = request.json.get('dataframe')
        df = pd.read_json(json.loads(dataframe_in_json))
        dfs[current_user.id] = df
        return "successfully populated analysis data"
    else :
        lock.acquire()
        df = dfs.get(current_user.id)
        lock.release()
        if df is None : 
            return redirect(url_for('views.home'))
        joy_count = (df['prediction'] == 'joy').sum()
        anger_count = (df['prediction'] == 'anger').sum()
        sadness_count = (df['prediction'] == 'sadness').sum()
        love_count = (df['prediction'] == 'love').sum()
        sympathy_count = (df['prediction'] == 'sympathy').sum()
        surprise_count = (df['prediction'] == 'surprise').sum()
        fear_count = (df['prediction'] == 'fear').sum()
        none_count = (df['prediction'] == 'none').sum()
        categories = ['joy', 'anger', 'sadness', 'love', 'sympathy', 'surprise', 'fear', 'none']
        counts = [joy_count, anger_count, sadness_count, love_count, sympathy_count, surprise_count, fear_count, none_count]
        counts = [int(count) for count in counts]
        tweetsJson = df['text'].to_json(orient='records')
        tweetsclsJson = df['prediction'].to_json(orient='records')
        tweetsLinksJson = df['tweetUrl'].to_json(orient='records')
        categories_json = json.dumps(categories)
        counts_json = json.dumps(counts)
        return render_template('ChartsWithTwitter.html', categories=categories_json, counts=counts_json, user=current_user,tweet = tweetsJson,emotion = tweetsclsJson,tweetsLink = tweetsLinksJson)
    


@views.route('/History')
def History():
    user_files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', user_files=user_files, user=current_user)
  
def twitter_scraping(keyword,matchType):
    try:
        user_semaphore.acquire()
        initialize_random_forest(f"{MODELS_DIR}Random_forest_final.joblib",f"{MODELS_DIR}bert_classifier_model.pth",  f"{MODELS_DIR}tokenizer.pkl",f"{MODELS_DIR}BiLSTM_model.h5" ,f"{MODELS_DIR}BiGRU_model.h5",f"{MODELS_DIR}tokenizer_config.json")
        df = get_twitterSentiments(keyword=keyword,searchType=matchType)
        return df
    finally:
        user_semaphore.release()
        
    
    
    
@views.route('/start-twitter-task',methods=['GET'])
def start_twitter_task():
    keyword = request.args.get('keyword')
    matchType = request.args.get('matchtype')
    with ThreadPoolExecutor(max_workers=1) as executor:
        future =  executor.submit(twitter_scraping,keyword,matchType)
        result = future.result()
        result = result.to_json()
        return jsonify({'dataframe': result})

@views.route('/start-file-task',methods=['POST'])
def start_file_task():
    initialize_random_forest(f"{MODELS_DIR}Random_forest_final.joblib",f"{MODELS_DIR}bert_classifier_model.pth",  f"{MODELS_DIR}tokenizer.pkl",f"{MODELS_DIR}BiLSTM_model.h5" ,f"{MODELS_DIR}BiGRU_model.h5",f"{MODELS_DIR}tokenizer_config.json")
    data = request.get_json()
    df = pd.read_json(json.dumps(data.get('dataframe')))
    classifications = get_sentiments(df['text'])
    df['prediction'] = classifications
    filename = data.get('file_name')
    filename = secure_filename(filename)
    new_filename = f'{filename.split(".")[0]}_predicted_{str(datetime.now()).replace(":", "-")}.csv' 
    save_location = os.path.join('predictedData', new_filename)
    df.to_csv(save_location, index=False)
    new_file = File(file_name=new_filename, user_id=current_user.id)
    db.session.add(new_file)
    db.session.commit()
    return jsonify({'filename' : new_filename })

@login_required
@views.route('/About-Us',methods = ['GET'])
def aboutUS():
    return render_template('AboutUs.html',user = current_user)
