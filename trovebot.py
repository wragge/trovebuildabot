import urllib
import httplib2
import json
import random
import twitter
import credentials
import re
import argparse
import datetime
import time
import logging

try:
    from file_locations_prod import *
except ImportError:
    pass
try:
    from file_locations_dev import *
except ImportError:
    pass

API_QUERY = 'http://api.trove.nla.gov.au/result?q={keywords}&zone=picture&key={key}&encoding=json&n={number}&s={start}&reclevel=full&sortby={sort}'
GREETING = 'Greetings human! Insert keywords. Use #luckydip for randomness.'
FAILED = "I didn't find anything for '{query}' so I found you this instead."
BOT_NAME = 'YourBotName'
NUC = 'YourNUC'


logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG,)


def lock():
    with open(LOCK_FILE, 'w') as lock_file:
        lock_file.write('1')
    return True


def unlock():
    with open(LOCK_FILE, 'w') as lock_file:
        lock_file.write('0')
    return True


def is_unlocked():
    with open(LOCK_FILE, 'r') as lock_file:
        if lock_file.read().strip() == '0':
            return True
        else:
            return False


def get_api_result(query):
    h = httplib2.Http()
    resp, content = h.request(query)
    try:
        json_data = json.loads(content)
    except ValueError:
        json_data = None
    return json_data


def get_start(text):
    nuc_query = 'nuc:"{}"'.format(NUC)
    text = '{} ({})'.format(nuc_query, text) if text else nuc_query
    query = API_QUERY.format(
        keywords=urllib.quote_plus(text),
        key=credentials.api_key,
        number=0,
        start=0,
        sort='relevance'
    )
    json_data = get_api_result(query)
    total = int(json_data['response']['zone'][0]['records']['total'])
    print total
    return random.randint(0, total)


def get_random_year():
    year = random.randint(START_YEAR, END_YEAR)
    return 'date:[{0} TO {0}]'.format(year)


def extract_params(query):
    if '#any' in query:
        query = query.replace('#any', '')
        query = '({})'.format(' OR '.join(query.split()))


def process_tweet(tweet):
    query = None
    random = False
    hello = False
    failed = False
    sort = 'relevance'
    trove_url = None
    text = tweet.text.strip()
    user = tweet.user.screen_name
    text = re.sub(r'@{} '.format(BOT_NAME), '', text, flags=re.IGNORECASE)
    text = text.replace(u'\u201c', '"').replace(u'\u201d', '"').replace(u'\u2019', "'")
    if re.search(r'\bhello\b', text, re.IGNORECASE):
        query = ''
        random = True
        hello = True
    else:
        if '#luckydip' in text:
            # Get a random article
            text = text.replace('#luckydip', '').strip()
            random = True
        if '#any' in text:
            text = text.replace('#any', '').strip()
            #print "'{}'".format(query)
            query = '({})'.format(' OR '.join(query.split()))
        else:
            query = text
    start = 0
    while trove_url is None:
        record = get_record(query, random, start, sort)
        if not record:
            if query:
                # Search failed
                random = True
                failed = True
                query = None
            else:
                # Something's wrong, let's just give up.
                message = "@{user} ERROR! Something went wrong. [:-(] {date}".format(user=user, date=datetime.datetime.now())
                break
        else:
            # Filter out 'coming soon' articles
            try:
                trove_url = record['troveUrl']
            except (KeyError, TypeError):
                pass
            # Don't keep looking forever
            if start < 60:
                start += 1
                time.sleep(1)
            else:
                message = "@{user} ERROR! Something went wrong. [:-(] {date}".format(user=user, date=datetime.datetime.now())
                record = None
                break
    if record:
        title = record['title']
        if hello:
            chars = 118 - (len(user) + len(GREETING) + 5)
            title = title[:chars]
            message = "@{user} {greeting} '{title}' {url}".format(user=user, greeting=GREETING, title=title.encode('utf-8'), url=trove_url)
        elif failed:
            failed_msg = FAILED.format(query = text)
            chars = 118 - (len(user) + len(failed_msg) + 6)
            title = title[:chars]
            message = "@{user} {failed} '{title}' {url}".format(user=user, failed=failed_msg, title=title.encode('utf-8'), url=trove_url)
        else:
            chars = 118 - (len(user) + 4)
            title = title[:chars]
            message = "@{user} '{title}' {url}".format(user=user, greeting=GREETING, title=title.encode('utf-8'), url=trove_url)
    return message


def get_record(text, random=False, start=0, sort='relevance'):
    if random:
        start = get_start(text)
    nuc_query = 'nuc:"{}"'.format(NUC)
    text = '{} ({})'.format(nuc_query, text) if text else nuc_query
    query = API_QUERY.format(
        keywords=urllib.quote_plus(text),
        key=credentials.api_key,
        number=1,
        start=start,
        sort=sort
    )
    print query
    json_data = get_api_result(query)
    try:
        record = json_data['response']['zone'][0]['records']['work'][0]
    except (KeyError, IndexError, TypeError):
        return None
    else:
        return record


def tweet_reply(api):
    if is_unlocked():
        lock()
        message = None
        with open(LAST_ID, 'r') as last_id_file:
            last_id = int(last_id_file.read().strip())
        #print api.VerifyCredentials()
        try:
            results = api.GetMentions(since_id=last_id)
        except:
            logging.exception('{}: Got exception on retrieving tweets'.format(datetime.datetime.now()))
        for tweet in results:
            if tweet.in_reply_to_screen_name == BOT_NAME:
                #print tweet.text
                try:
                    message = process_tweet(tweet)
                except:
                    logging.exception('{}: Got exception on process_tweet'.format(datetime.datetime.now()))
                    message = None
                if message:
                    try:
                        print message
                        api.PostUpdate(message, in_reply_to_status_id=tweet.id)
                    except:
                        logging.exception('{}: Got exception on sending tweet'.format(datetime.datetime.now()))
                time.sleep(20)
        if results:
            with open(LAST_ID, 'w') as last_id_file:
                last_id_file.write(str(max([x.id for x in results])))
        unlock()


def check_thumbnail(record):
    thumbnail = ''
    for link in record['identifier']:
        if link['type'] == 'url' and link['linktype'] == 'thumbnail':
            thumbnail = link['value']
    return thumbnail


def tweet_random(api):
    trove_url = None
    while not trove_url:
        record = get_record(text='', random=True)
        try:
            trove_url = record['troveUrl']
        except (KeyError, TypeError):
            pass
        time.sleep(1)
    #alert = record['type'][0]
    #chars = 118 - (len(alert) + 5)
    #thumbnail = check_thumbnail(record)
    chars = 117
    title = record['title'][:chars]
    message = "'{title}' {url}".format(title=title.encode('utf-8'), url=trove_url)
    print message
    api.PostUpdate(message)

if __name__ == '__main__':
    api = twitter.Api(
        consumer_key=credentials.consumer_key,
        consumer_secret=credentials.consumer_secret,
        access_token_key=credentials.access_token_key,
        access_token_secret=credentials.access_token_secret
    )
    parser = argparse.ArgumentParser()
    parser.add_argument('task')
    args = parser.parse_args()
    if args.task == 'reply':
        tweet_reply(api)
    elif args.task == 'random':
        tweet_random(api)
