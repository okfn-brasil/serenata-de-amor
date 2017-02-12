import os
import sys
import time
import requests
from py2neo import Graph, Node, Relationship

graph = Graph()

graph.run("CREATE CONSTRAINT ON (u:User) ASSERT u.username IS UNIQUE")
graph.run("CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE")
graph.run("CREATE CONSTRAINT ON (h:Hashtag) ASSERT h.name IS UNIQUE")

TWITTER_BEARER = os.environ["TWITTER_BEARER"]

headers = dict(accept="application/json", Authorization="Bearer " + TWITTER_BEARER)

payload = dict(
    count=100,
    result_type="recent",
    lang="en",
    q=sys.argv[1]
)

base_url = "https://api.twitter.com/1.1/search/tweets.json?"


def find_tweets(since_id):
    payload["since_id"] = since_id
    url = base_url + "q={q}&count={count}&result_type={result_type}&lang={lang}&since_id={since_id}".format(**payload)

    r = requests.get(url, headers=headers)
    tweets = r.json()["statuses"]

    return tweets


def upload_tweets(tweets):
    for t in tweets:
        u = t["user"]
        e = t["entities"]

        tweet = Node("Tweet", id=t["id"])
        graph.merge(tweet)
        tweet["text"] = t["text"]
        tweet.push()

        user = Node("User", username=u["screen_name"])
        graph.merge(user)

        graph.merge(Relationship(user, "POSTS", tweet))

        for h in e.get("hashtags", []):
            hashtag = Node("Hashtag", name=h["text"].lower())
            graph.merge(hashtag)
            graph.merge(Relationship(hashtag, "TAGS", tweet))

        for m in e.get('user_mentions', []):
            mention = Node("User", username=m["screen_name"])
            graph.merge(mention)
            graph.merge(Relationship(tweet, "MENTIONS", mention))

        reply = t.get("in_reply_to_status_id")

        if reply:
            reply_tweet = Node("Tweet", id=reply)
            graph.merge(reply_tweet)
            graph.merge(Relationship(tweet, "REPLY_TO", reply_tweet))

        ret = t.get("retweeted_status", {}).get("id")

        if ret:
            retweet = Node("Tweet", id=ret)
            graph.merge(retweet)
            graph.merge(Relationship(tweet, "RETWEETS", retweet))


since_id = -1

while True:
    try:
        tweets = find_tweets(since_id=since_id)

        if not tweets:
            print("No tweets found.")
            time.sleep(60)
            continue

        since_id = tweets[0].get("id")
        upload_tweets(tweets)

        print("{} tweets uploaded!".format(len(tweets)))
        time.sleep(60)

    except Exception as e:
        print(e)
        time.sleep(60)
        continue
