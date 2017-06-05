import praw
import time
import traceback
import re
import threading
import sys

import config

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
				self.tPrint("running")
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

class SubmissionThread(RedditThread):
	def run(self):
		reddit = self.setupReddit()
		while 1:
			try:
				self.tPrint("running")
				time.sleep(1)
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
