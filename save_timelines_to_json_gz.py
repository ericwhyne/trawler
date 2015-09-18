#!/usr/bin/env python

"""
This script downloads all available Tweets for a given list of
usernames.

The script takes as input a text file which lists one Twitter username
per line of the file.  The script creates a [username].tweets file for
each username specified in the directory.

Your Twitter OAuth credentials should be stored in the file
twitter_oauth_settings.py.
"""

# Standard Library modules
import argparse
import codecs
import os
import sys
import gzip

# Third party modules
from twython import Twython, TwythonError

# Local modules
from twitter_crawler import (CrawlTwitterTimelines, RateLimitedTwitterEndpoint, 
                             get_console_info_logger, get_screen_names_from_file, save_tweets_to_json_file)
try:
    from twitter_oauth_settings import access_token, access_token_secret, consumer_key, consumer_secret
except ImportError:
    print "You must create a 'twitter_oauth_settings.py' file with your Twitter API credentials."
    print "Please copy over the sample configuration file:"
    print "  cp twitter_oauth_settings.sample.py twitter_oauth_settings.py"
    print "and add your API credentials to the file."
    sys.exit()


def main():
    # Make stdout output UTF-8, preventing "'ascii' codec can't encode" errors
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('id_file')
    parser.add_argument('output_loc')
    parser.add_argument('--token_file',dest='token_file',default=None)
    args = parser.parse_args()

    logger = get_console_info_logger()

    #Optionally pass as a parameter
    #There has to be a more elegant way to combine this with the default behavior -- tomorrow's problem though
    oauth_settings_file_loc = args.token_file
    if oauth_settings_file_loc:
        print "Using tokens from:", oauth_settings_file_loc
        exec(open(oauth_settings_file_loc).read())

    ACCESS_TOKEN = Twython(consumer_key, consumer_secret, oauth_version=2).obtain_access_token()
    twython = Twython(consumer_key, access_token=ACCESS_TOKEN)
    crawler = CrawlTwitterTimelines(twython, logger)

    twitter_ids = get_screen_names_from_file(args.id_file)
    twitter_ids.reverse() #HARDCODE
    output_loc = args.output_loc

    tempfile_loc = 'tmp/'
    os.system('mkdir -p '+tempfile_loc)
    
    #load previously broken ID files so we don't try to read them again
    broken_ids = set([]) #Defaults to an empty set
    try:
        broken_ids = set([long(x).strip() for x in open(tempfile_loc + '404d').readlines()])
    except:
        pass
    try:
        broken_ids = broken_ids.union(set([long(x).strip() for x in open(tempfile_loc + '401d').readlines()]))
    except:
        pass
    
    for twitter_id in twitter_ids:
        if twitter_id in broken_ids:
            print '%s was previously inaccessible, not trying to download.' % twitter_id
            continue
        tweet_filename = output_loc + "%s.tweets.gz" % twitter_id
        if os.path.exists(tweet_filename):
            logger.info("File '%s' already exists - will not attempt to download Tweets for '%s'" % (tweet_filename, twitter_id))
        else:
            try:
                tweets = crawler.get_all_timeline_tweets_for_id(twitter_id)
            except TwythonError as e:
                print "TwythonError: %s" % e
                if e.error_code == 404:
                    logger.warn("HTTP 404 error - Most likely, Twitter user '%s' no longer exists" % twitter_id)
                    with open(tempfile_loc + '404d','a') as OUT:
                        OUT.write('%s\n' % twitter_id)
                elif e.error_code == 401:
                    logger.warn("HTTP 401 error - Most likely, Twitter user '%s' no longer publicly accessible" % twitter_id)
                    with open(tempfile_loc + '401d','a') as OUT:
                        OUT.write('%s\n' % twitter_id)
                else:
                    # Unhandled exception
                    print e 
                    #Reconnect and try again
                    twython = Twython(consumer_key, access_token=ACCESS_TOKEN)
                    crawler = CrawlTwitterTimelines(twython, logger)
            else:
                save_tweets_to_json_file(tweets, tweet_filename, gzip_out=True)


if __name__ == "__main__":
    main()
