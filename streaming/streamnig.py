#!/usr/bin/python
# sample of how to access 1% streamnig twitter api
import json
import os
import yaml
from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream

tokens = yaml.safe_load(open(os.path.expanduser("~") + "/.trawler/default.yaml"))
ACCESS_TOKEN = tokens['access_token']
ACCESS_SECRET = tokens['access_token_secret']
CONSUMER_KEY = tokens['consumer_key']
CONSUMER_SECRET = tokens['consumer_secret']

oauth = OAuth(ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
twitter_stream = TwitterStream(auth=oauth)
iterator = twitter_stream.statuses.sample()
tweet_count = 1000
for tweet in iterator:
    tweet_count -= 1
    print json.dumps(tweet)
    if tweet_count <= 0:
        break
