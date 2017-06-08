import praw
import time
import traceback
import re
import threading
import sys

import config
import database

REDDITUSERNAME     = config.redditUsername
REDDITPASSWORD     = config.redditPassword
REDDITUSERAGENT    = config.redditUserAgent
REDDITAPPID        = config.redditAppId
REDDITAPPSECRET    = config.redditAppSecret
REDDITREFRESHTOKEN = config.redditRefreshToken

class RedditThread(threading.Thread):
	def tPrint(self, s):
		t = time.strftime("%H:%M:%S", time.gmtime())
		sys.stdout.write("[{} {:17}] {}\n".format(t, self.getName(), s))

	def setupReddit(self):
		try:
			self.tPrint("Setting up reddit")
			reddit = praw.Reddit(client_id=REDDITAPPID,
								 client_secret=REDDITAPPSECRET,
								 username=REDDITUSERNAME,
								 password=REDDITPASSWORD,
								 user_agent=REDDITUSERAGENT,
								 refresh_token=REDDITREFRESHTOKEN)
			self.tPrint("Reddit successfully set up")
			return reddit
		except Exception as e:
			self.tPrint("Error setting up Reddit: " + str(e))

class MessageThread(RedditThread):
	def run(self):
		reddit = self.setupReddit()
		while 1:
			try:

				for item in reddit.inbox.unread(limit=None):
					if isinstance(item, praw.models.Message):
						self.tPrint(vars(item))

				time.sleep(1)
			except Exception as e:
				traceback.print_exc()

class CommentThread(RedditThread):
	def run(self):
		reddit = self.setupReddit()
		while 1:
			try:
				self.tPrint("running")
				time.sleep(1)
			except Exception as e:
				traceback.print_exc()

REPLY_TEMPLATE = '''
{}

Recruitment posts should follow the following rules:

1. Clan Recruitment Posts must be flaired accordingly by using the "Clan" flair.
2. The title of the post must begin with: "[Clan Recruitment - clancode]"
3. Over 72 hours have passed since your clan's last recruitment post.

---

^^Beep ^^boop, ^^I'm ^^a ^^TapTitans2 ^^bot! ^^\([Github](https://github.com/colblitz/Dex1000)) ^^Please ^^PM ^^/u/colblitz ^^with ^^any ^^questions.
'''

POST_TITLE_FORMATTING = "This post is being removed for being a recruitment post without the proper formatting."
TOO_SOON = "This post is being removed for violating rule 3. Please wait {} before posting another recruitment post for clan {}"

def formatTime(t):
	return "{} second".format(t)

def process_submission(submission):
	postId = submission.id
	postDate = int(submission.created_utc)
	clanCode = None

	print "postId {} postDate {} clanCode {}".format(postId, postDate, clanCode)

	isPotentialClanPost = any(w in submission.title.lower() for w in ['clan', 'recruit'])

	print "isPotentialClanPost: " + str(isPotentialClanPost)

	m = re.compile('\[clan recruitment - \w+\].*').match(submission.title.lower())
	if isPotentialClanPost and not m:
		print "bad formatting"
		## Clan post with bad formatting
		reply = REPLY_TEMPLATE.format(POST_TITLE_FORMATTING)
		submission.reply(reply)
		submission.delete()
		return

	if m:
		clanCode = m.group(1)
		lastPost = database.getLastClanPostDate(clanCode)
		timeSinceLastPost = postDate - lastPost
		print "timeSinceLastPost: "  + str(timeSinceLastPost)
		if lastPost and timeSinceLastPost < 1000:
			print "too soon"
			## Posting again too soon
			reply = REPLY_TEMPLATE.format(TOO_SOON.format(formatTime(timeSinceLastPost), clanCode))
			submission.reply(reply)
			submission.delete()
			return

		print "insert clan " + clanCode
		database.insertClan(clanCode)

	print "insert post"
	database.insertPost(postId, postDate, clanCode)

class SubmissionThread(RedditThread):
	def run(self):
		reddit = self.setupReddit()
		while 1:
			try:
				subreddit = reddit.subreddit('taptitanstest')
				for submission in subreddit.stream.submissions():
					process_submission(submission)
			except Exception as e:
				traceback.print_exc()

if __name__ == '__main__':
	messageThread = MessageThread(name="MessageThread")
	messageThread.daemon = True
	messageThread.start()
	commentThread = CommentThread(name="CommentThread")
	commentThread.daemon = True
	commentThread.start()
	submissionThread = SubmissionThread(name="SubmissionThread")
	submissionThread.daemon = True
	submissionThread.start()

	while True:
	    time.sleep(1)
