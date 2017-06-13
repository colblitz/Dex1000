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

DATABASE = config.databaseFile

class RedditThread(threading.Thread):
	reddit = None
	db = None

	def tPrint(self, s):
		t = time.strftime("%H:%M:%S", time.gmtime())
		sys.stdout.write("[{} {:17}] {}\n".format(t, self.getName(), s))
		sys.stdout.flush()

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

BAD_MESSAGE_TEMPLATE = '''
{}

Go to []() for formatting and examples.

---

^^Beep ^^boop, ^^I'm ^^a ^^TapTitans2 ^^bot! ^^\([Github](https://github.com/colblitz/Dex1000)) ^^Please ^^PM ^^/u/colblitz ^^with ^^any ^^questions.
'''

CLAN_FIELDS = {
	'clanquest': 'clanQuest',
	'openpositions': 'openPositions',
	'rank': 'rank',
	'name': 'name',
	'redditcontact': 'redditContact',
	'othercontact': 'otherContact',
	'requirements': 'requirements',
	'description': 'description'
}
CLAN_FIELDS_KEYS = list(CLAN_FIELDS.keys())

INT_FIELDS = ['clanquest', 'openpositions', 'rank']


CLAN_DIRECTORY_TAG = "@@ AUTOGENERATED - Do not edit anything below this line @@"
CLAN_DIRECTORY = '''

----

Clan Name | Code | Rank | CQ | Open | Reddit Contact | Other Contact | Requirements | Description
---|---|---|---|---|---|---|---|---
{}
'''
CLAN_DIRECTORY_ROW = "{} | {} | {} | {} | {} | {} | {} | {} | {} \n"

SUBREDDIT = 'TapTitans2'

class MessageThread(RedditThread):
	def logMessage(self, message):
		self.tPrint("## M ## {} | {} | {}".format(
			message.id,
			message.author,
			message.subject))

	def updateWiki(self):
		self.tPrint(" - Attempt to update wiki")
		cd = self.reddit.subreddit(SUBREDDIT).wiki['clan_directory']
		currentPage = cd.content_md
		try:
			start = currentPage.index(CLAN_DIRECTORY_TAG)

			## TODO: clean this up, add /u/ for reddit names?
			clanInfo = database.getClanInformation(self.db)
			rearranged = [[i[4], i[0], i[3], i[1], i[2], i[5], i[6], i[7], i[8]] for i in clanInfo]
			cleaned = [['' if v is None else v for v in i] for i in rearranged]
			rows = [CLAN_DIRECTORY_ROW.format(*i) for i in cleaned]
			newDirectory = CLAN_DIRECTORY.format(''.join(rows))

			newPage = currentPage[:start] + CLAN_DIRECTORY_TAG + newDirectory
			cd.edit(newPage)
			self.tPrint(" - Wiki update successful")
		except ValueError:
			## TODO: Not found, PM colblitz
			pass
		except Exception as e:
			pass

	def processMessage(self, message):
		if database.messageExists(self.db, message.id):
			return
		self.logMessage(message)

		subject = message.subject.lower()
		if subject == "username mention":
			self.tPrint(' - Username mention')
		elif "add clan" in subject:
			self.tPrint(' - Add clan request')
			m = re.compile('.*\[(\w+)\].*').match(subject)
			if m:
				clanCode = m.group(1)
				database.insertClan(self.db, clanCode)
				message.reply("Clan added successfully")
		elif "update" in subject:
			self.tPrint(' - Update request')
			m = re.compile('.*\[(\w+)\].*').match(subject)
			if m:
				clanCode = m.group(1)
				## TODO: check author
				# author = message.author.name.lower()

				## get fields
				updateValues = {}
				for line in message.body.split('\n'):
					parts = line.split('|')
					key = parts[0].strip().lower()
					## TODO: make this better - individual regexes?
					if key in CLAN_FIELDS_KEYS:
						updateValues[CLAN_FIELDS[key]] = str('|'.join(parts[1:]))
						if key in INT_FIELDS:
							updateValues[CLAN_FIELDS[key]] = int('|'.join(parts[1:]))
				if updateValues:
					try:
						self.tPrint(" - " + str(updateValues))
						database.updateClan(self.db, clanCode, updateValues)
						message.reply("Update successful")
						self.tPrint(' - Update successful')
					except Exception as e:
						self.tPrint(" - Error updating clan {} with values {}".format(clanCode, str(updateValues)))
					self.updateWiki()
				else:
					## could not get any update values
					message.reply(BAD_MESSAGE_TEMPLATE.format("Could not parse any update values"))
			else:
				## Could not find clan code, error
				message.reply(BAD_MESSAGE_TEMPLATE.format("Could not parse clan code"))
			message.mark_read()
			database.markMessage(self.db, message.id, True)

	def run(self):
		self.reddit = self.setupReddit()
		self.db = database.get_db(DATABASE)
		while 1:
			self.tPrint("Start of loop")
			try:
				for item in self.reddit.inbox.stream():
					self.processMessage(item)
				# for item in reddit.inbox.unread(limit=None):
				# 	if isinstance(item, praw.models.Message):
				# 		process_message(item)
			except Exception as e:
				self.tPrint("Error: " + str(e))
				traceback.print_exc()
				time.sleep(10)

class CommentThread(RedditThread):
	def logComment(self, comment):
		pass

	def processComment(self, comment):
		pass

	def run(self):
		self.reddit = self.setupReddit()
		self.db = database.get_db(DATABASE)
		while 1:
			self.tPrint("Start of loop")
			try:
				subreddit = self.reddit.subreddit(SUBREDDIT)
				for comment in subreddit.stream.comments():
					self.processComment(comment)
			except Exception as e:
				self.tPrint("Error: " + str(e))
				traceback.print_exc()
				time.sleep(10)

POST_REPLY_TEMPLATE = '''
{}

Recruitment posts should follow the following rules:

1. The title of the post must begin with: "[Clan Recruitment - clancode]". For example, "[Clan Recruitment - 2j8ei] Recruiting for Test Clan!" would be an acceptable title.
2. Clan Recruitment Posts must be flaired accordingly by using the "Clan" flair.
3. Over 100 posts on the subreddit have been submitted or 72 hours have passed since your last recruitment post.

---

^^Beep ^^boop, ^^I'm ^^a ^^TapTitans2 ^^bot! ^^\([Github](https://github.com/colblitz/Dex1000)) ^^Please ^^PM ^^/u/colblitz ^^with ^^any ^^questions.
'''

POST_TITLE_FORMATTING = "This post is being removed for being a recruitment post without the proper formatting. If this is not a recruitment post, please pm /u/colblitz."
TOO_SOON = "This post is being removed for violating rule 3. Please wait {} or for {} more posts before posting another recruitment post for clan {}"
# CLAN_POST_DELAY = 60*60*24*4
CLAN_POST_DELAY = 60*5

def formatTime(t):
	if t < 60:
		return "{} seconds".format(t)
	if t < 60 * 60:
		return "{} minutes".format(t / 60)
	else:
		return "{} hours".format(t / 60 / 60)

class SubmissionThread(RedditThread):
	def logSubmission(self, submission):
		self.tPrint("## S ## {} | {} | {} | {}".format(
			submission.id,
			int(submission.created_utc),
			submission.author,
			submission.title.encode('utf-8')))

	def processSubmission(self, submission):
		if database.postExists(self.db, submission.id):
			return
		self.logSubmission(submission)

		if int(submission.created_utc) < 1497163543:
			database.insertPost(self.db, submission.id, int(submission.created_utc))
			return

		## TODO: make this better
		title = submission.title.lower()
		isPotentialClanPost = sum([w in title for w in ['clan', 'recruit', 'cq']]) > 1
		# isPotentialClanPost = all(w in submission.title.lower() for w in ['recruit'])

		m = re.compile('\[clan recruitment\s*-\s*(.+)\s*\].*').match(submission.title.lower())
		## Clan post with bad formatting
		if isPotentialClanPost and not m:
			self.tPrint(" - Bad formatting")
			reply = POST_REPLY_TEMPLATE.format(POST_TITLE_FORMATTING)
			submission.reply(reply)
			submission.mod.remove()
			return

		if m:
			clanCodes = m.group(1)
			postDate = int(submission.created_utc)
			for clanCode in re.findall('(\w+)', clanCodes):
				lastPost = database.getLastClanPost(self.db, clanCode)
				timeSinceLastPost = postDate - lastPost[0] if lastPost[0] else sys.maxint
				postsSinceLastPost = database.getPostsSince(self.db, lastPost[1]) if lastPost[1] else sys.maxint
				self.tPrint(" - {} timeSinceLastPost: {} postsSinceLastPost {}".format(clanCode, timeSinceLastPost, postsSinceLastPost))

				## Check for posting too soon
				if (lastPost and
					timeSinceLastPost > 0 and timeSinceLastPost < CLAN_POST_DELAY and
					postsSinceLastPost < 100):
					self.tPrint(" - Posting too soon")
					reply = POST_REPLY_TEMPLATE.format(TOO_SOON.format(
						formatTime(CLAN_POST_DELAY - timeSinceLastPost),
						100 - postsSinceLastPost,
						clanCode))
					submission.reply(reply)
					submission.mod.remove()
					return

				self.tPrint(" - Inserting clan " + clanCode)
				database.insertClan(self.db, clanCode)

		database.insertPost(self.db, submission.id, int(submission.created_utc), m.group(1) if m else None)

	def run(self):
		self.reddit = self.setupReddit()
		self.db = database.get_db(DATABASE)
		while 1:
			self.tPrint("Start of loop")
			try:
				subreddit = self.reddit.subreddit(SUBREDDIT)
				for submission in subreddit.stream.submissions():
					self.processSubmission(submission)
			except Exception as e:
				self.tPrint("Error: " + str(e))
				traceback.print_exc()
				time.sleep(10)

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
