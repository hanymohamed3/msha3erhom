import time
from  selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as waiter
from selenium.webdriver.common.by import By
import pandas as pd 

from RandomForestForBatches.Preprocessing.Preprocessing import *
#from Marbert.BertClassifier import get_sentiment
from RandomForestForBatches.RandomForest import get_sentiments
from threading import Lock
from collections import namedtuple

global lock
lock = Lock()

Tweet = namedtuple('Tweet',['tweet','url'])
    

def get_twitterSentiments(keyword,searchType):
    global profiles
    options = webdriver.ChromeOptions()
    path = "C:\\My Projects\\Masha'erohom\\chromedriver.exe"
    options.add_argument('--no-sandbox')
    # options.add_argument('--headless')
    # user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    # options.add_argument(f'user-agent={user_agent}')
    options.add_argument('--disable-gpu')
    profilePath = "C:\\My Projects\\Masha'erohom\\User Data\\Default"
    options.add_argument(f"--user-data-dir={profilePath}")
    chrome_driver = webdriver.Chrome(service=Service(path), options=options)
    
    tweets =[]
    if searchType == 'all':
        keyword = '('+' AND '.join(keyword.split()) +')'
    elif searchType == 'exact':
        keyword = f'"{keyword}"'
    else:
        keyword = '('+' OR '.join(keyword.split())+')'
    try :
        chrome_driver.get(f'https://twitter.com/search?q={keyword}%20lang%3Aar%20-filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top')
        wait = waiter(chrome_driver,15)
        
        tweets = set()
        i = 0 
        while len(tweets) <= 45 :
            if i >= 50:
                break
            tweetsWebElements = wait.until(EC.presence_of_all_elements_located((By.XPATH,'//article[contains(@data-testid,"tweet")]')))
            addtweets = []
            try:
                
                addtweets = [Tweet(tweet= clean_for_twitter(tweetelem.find_element(By.XPATH, ".//div[@lang='ar']").text) , url= tweetelem.find_element(By.XPATH, ".//a[contains(@href,'/status/')]").get_attribute("href")) for tweetelem in tweetsWebElements]
            except:
                pass
            for t in addtweets:
                tweets.add(t)
            i = i+1
            time.sleep(0.3)
            chrome_driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            
            
    except Exception as e:
        print(e)
    finally:
        chrome_driver.quit()
    return pd.DataFrame({'text':[tweet.tweet for tweet in tweets],'tweetUrl':[tweet.url for tweet in tweets],'prediction':get_sentiments([tweet.tweet for tweet in tweets])})


def clean_for_twitter(text):
    text=remove_emails(text)
    text=remove_URLs(text)
    text=remove_mentions(text)
    text= hashtags_to_words(text)
    text= remove_newlines(text)
    return text 
    