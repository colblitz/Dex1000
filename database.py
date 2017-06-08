import sqlite3

import config

DATABASE = config.databaseFile
INIT_SCRIPT = """
DROP TABLE IF EXISTS clans;
DROP TABLE IF EXISTS posts;
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
	postId text primary key not null,
	date integer,
	clanCode text
);
CREATE TABLE clanPosters (
	clanCode text,
	username text
);
"""

db = None

def get_db():
	global db
	if db is None:
		db = sqlite3.connect(DATABASE)
		db.row_factory = sqlite3.Row
	return db

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv

def init_db():
	db = get_db()
	db.cursor().executescript(INIT_SCRIPT)

def insertPost(postId, date, clanCode = None):
	if clanCode:
		get_db().cursor().execute("INSERT OR REPLACE INTO posts VALUES (?, ?, ?)", (postId, date, clanCode))
	else:
		get_db().cursor().execute("INSERT OR REPLACE INTO posts(postId, date) VALUES (?, ?)", (postId, date))
	get_db().commit()

def postExists(postId):
	if query_db("SELECT postId FROM posts WHERE postId = ?", (postId,)):
		return True
	return False

def getLastClanPostDate(clanCode):
	return query_db("SELECT MAX(date) FROM posts WHERE clanCode = ?", (clanCode,))[0][0]

def clanExists(clanCode):
	if query_db("SELECT clanCode FROM clans WHERE clanCode = ?", (clanCode,)):
		return True
	return False

def insertClan(clanCode):
	get_db().cursor().execute("INSERT OR IGNORE INTO clans(clanCode) VALUES (?)", (clanCode,))
	get_db().commit()

def updateClan(clanCode, args={}):
	get_db().cursor().execute(
		"UPDATE clans SET " + ', '.join(key + ' = ?' for key in args) + " WHERE clanCode = ?",
		args.values() + [clanCode])
	get_db().commit()

def insertClanPoster(clanCode, username):
	get_db().cursor().execute("INSERT INTO clanPosters VALUES (?, ?)", (clanCode, username))
	get_db().commit()

def isClanPoster(clanCode, username):
	if query_db("SELECT username FROM clanPosters WHERE clanCode = ? AND username = ?", (clanCode, username)):
		return True
	return False

def getClanPosters(clanCodes):
	clanPosters = {}
	for row in query_db("SELECT clanCode, username FROM clanPosters WHERE clanCode IN (%s)" % ", ".join(clanCodes)):
		clanCode = row['clanCode']
		username = row['username']
		if clanCode not in clanPosters:
			clanPosters[clanCode] = []
		clanPosters[clanCode].append(username)
	return clanPosters

if __name__ == '__main__':
	init_db()
	insertClan("asdf")
	updateClan("asdf", {"clanQuest" : 5, "name" : "test"})
	insertPost("235235", 123123, "252323")
	insertPost("whf8eh48g", 974235323, "s894fh4f")
	insertPost("iughse4i23r", 984235)
	print postExists("235235")
	print postExists("giuhsi4ugh734")
	print getLastClanPostDate("252323")
	print getLastClanPostDate("igshewg3")