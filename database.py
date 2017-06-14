import sqlite3
import os

import config

DATABASE = config.databaseFile
INIT_SCRIPT = """
DROP TABLE IF EXISTS clans;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS clanPosters;

CREATE TABLE clans (
	clanCode text primary key not null,
	clanQuest integer,
	openPositions integer,
	rank integer,
	name text,
	redditContact text,
	otherContact text,
	requirements text,
	description text
);
CREATE TABLE posts (
	postId text not null,
	date integer,
	clanCode text
);
CREATE TABLE messages (
	messageId text primary key not null,
	date integer,
	read integer
);
CREATE TABLE clanPosters (
	clanCode text,
	username text
);
"""

# db = None

cwd = os.path.dirname(os.path.abspath(__file__))

def get_db(database):
	# global db
	# if db is None:
	db = sqlite3.connect(cwd + "/" + database)
	db.row_factory = sqlite3.Row
	return db

def query_db(db, query, args=(), one=False):
	cur = db.execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv

def init_db(database):
	db = get_db(database)
	db.cursor().executescript(INIT_SCRIPT)

def insertPost(db, postId, date, clanCode = None):
	if clanCode:
		db.cursor().execute("INSERT INTO posts VALUES (?, ?, ?)", (postId, date, clanCode))
	else:
		db.cursor().execute("INSERT INTO posts(postId, date) VALUES (?, ?)", (postId, date))
	db.commit()

def postExists(db, postId):
	if query_db(db, "SELECT postId FROM posts WHERE postId = ?", (postId,)):
		return True
	return False

def getLastClanPost(db, clanCode):
	return query_db(db, "SELECT MAX(date), postID FROM posts WHERE clanCode = ?", (clanCode,))[0]

def getLastClanPostDate(db, clanCode):
	return query_db(db, "SELECT MAX(date) FROM posts WHERE clanCode = ?", (clanCode,))[0][0]

def getPostsSince(db, s):
	return query_db(db, "SELECT count(*) FROM posts where posts.postID > ?", (s,))[0][0]

def getPostsBetween(db, s, e):
	return query_db(db, "SELECT count(*) FROM posts where posts.postID > ? AND posts.postID < ?", (s, e))[0][0]

def insertMessage(db, messageId, date):
	db.cursor().execute("INSERT INTO messages VALUES (?, ?)", (messageId, date))
	db.commit()

def messageExists(db, messageId):
	if query_db(db, "SELECT messageId FROM messages WHERE messageId = ?", (messageId,)):
		return True
	return False

def markMessage(db, messageId, read):
	db.cursor().execute("UPDATE messages SET read = ? WHERE messageId = ?", (read, messageId))
	db.commit()

def clanExists(db, clanCode):
	if query_db(db, "SELECT clanCode FROM clans WHERE clanCode = ?", (clanCode,)):
		return True
	return False

def insertClan(db, clanCode):
	db.cursor().execute("INSERT OR IGNORE INTO clans(clanCode) VALUES (?)", (clanCode,))
	db.commit()

def updateClan(db, clanCode, args={}):
	db.cursor().execute(
		"UPDATE clans SET " + ', '.join(key + ' = ?' for key in args) + " WHERE clanCode = ?",
		args.values() + [clanCode])
	db.commit()

def getClanInformation(db):
	return query_db(db, "SELECT * FROM clans WHERE name IS NOT NULL ORDER BY clanQuest DESC")

def insertClanPoster(db, clanCode, username):
	db.cursor().execute("INSERT INTO clanPosters VALUES (?, ?)", (clanCode, username))
	db.commit()

def isClanPoster(db, clanCode, username):
	if query_db(db, "SELECT username FROM clanPosters WHERE clanCode = ? AND username = ?", (clanCode, username)):
		return True
	return False

def getClanPosters(db, clanCodes):
	clanPosters = {}
	for row in query_db(db, "SELECT clanCode, username FROM clanPosters WHERE clanCode IN (%s)" % ", ".join(clanCodes)):
		clanCode = row['clanCode']
		username = row['username']
		if clanCode not in clanPosters:
			clanPosters[clanCode] = []
		clanPosters[clanCode].append(username)
	return clanPosters

if __name__ == '__main__':
	init_db(DATABASE)
	# init_db()
	# insertClan("asdf")
	# updateClan("asdf", {"clanQuest" : 5, "name" : "test"})
	# insertPost("235235", 123123, "252323")
	# insertPost("whf8eh48g", 974235323, "s894fh4f")
	# insertPost("iughse4i23r", 984235)
	# print postExists("235235")
	# print postExists("giuhsi4ugh734")
	# print getLastClanPostDate("252323")
	# print getLastClanPostDate("igshewg3")
	# print getClanInformation()
