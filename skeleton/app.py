######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
from datetime import date
#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'PASSWORD'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		email=request.form.get('email')
		password=request.form.get('password')
		birth_date=request.form.get('birth_date')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender,password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')"
		.format(first_name, last_name, email, birth_date, hometown, gender,password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("WRONG EMAIL couldn't find all tokens")
		#render_template('register.html', supress='False')
		return flask.redirect(flask.url_for('register_error'))

@app.route('/registererror')
def register_error():
		return render_template('registererror.html', supress='False')	


def getAllUser_IDS():
	cursor = conn.cursor()
	cursor.execute("""SELECT user_id from Users """)
	records = cursor.fetchall()
	# all user ids in list form
	records_list = [x[0] for x in records]
	return records_list

def getAllUser_Emails():
	cursor = conn.cursor()
	cursor.execute("""SELECT email from Users """)
	records = cursor.fetchall()
	# all user ids in list form
	records_list = [x[0] for x in records]
	return records_list

def getUsersPhotos(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format( user_id))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getCommentsOnPhotos(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, text FROM Comments WHERE photo_id = '{0}'".format(photo_id))
	records = cursor.fetchall()
	# all user ids in list form
	records_list = [ [x[0], x[1]] for x in records]
	return records_list

def getOnePhotoInfo(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE photo_id = '{0}'".format(photo_id))
	return cursor.fetchall()

def getUseridfromphoto(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Photos WHERE photo_id = '{0}'".format(photo_id))
	records = cursor.fetchall()
	# all user ids in list form
	records_list = [ x[0] for x in records]
	return records_list

def getAlbumsPhotos(album_name):
	cursor = conn.cursor()
	cursor.execute(" SELECT data, photo_id, caption FROM Photos WHERE album_name = '{0}'".format(album_name))
	return cursor.fetchall()

def getUsersAlbums(user_id):
	cursor = conn.cursor()
	cursor.execute("Select album_name FROM Albums WHERE user_id = '{0}'".format(user_id))
	records = cursor.fetchall()
	records_list = [x[0] for x in records]
	return records_list

def getUsersFriends(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1= '{0}'".format(user_id))
	records = cursor.fetchall()
	records_list = [x[0] for x in records]
	return records_list

def getUserEmailFromUser_Id(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(user_id))
	records = cursor.fetchall()
	records_list = [x[0] for x in records]
	return records_list
	
def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getAlbumIDFromUserId(user_id, album_name):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id FROM Albums WHERE user_id = '{0}' AND album_name = '{1}' ".format(user_id, album_name))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

def insertLike(user_id, photo_id):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Likes (photo_id, user_id) VALUES (%s, %s)", (photo_id, user_id))
	conn.commit()
	return

def getLikesCountFor1Photo(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE photo_id = '{0}'".format(photo_id))
	num_likes = cursor.fetchall()
	return num_likes[0]

def getUserLikeListFor1Photo(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Likes WHERE photo_id = '{0}'".format(photo_id))
	user_ids = cursor.fetchall()
	user_id_list = [x[0] for x in user_ids]
	user_email_list = [ getUserEmailFromUser_Id(y) for y in user_id_list]
	return user_email_list

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		data =imgfile.read()
		album_name= request.form.get('album_name')
		album_id = getAlbumIDFromUserId (user_id, album_name)
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (data, user_id, caption, albums_id, album_name) VALUES (%s, %s, %s, %s, %s ) ''' ,(data,user_id, caption, album_id, album_name))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(user_id), Albums = getUsersAlbums(user_id),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		print(" Arriving at GET upload method")
		return render_template('upload.html', Albums = getUsersAlbums(user_id))
#end photo uploading code

#show all photos
#@app.route('/showphotos', method=['GET'])
#def showPhotos():
#	cursor = conn.cursor()
#	photo_id=request.form.get('photo_id')
#	cursor.execute("SELECT data, photo_id, caption FROM Photos = '{0}'".format(photo_id))
#	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]


@app.route ("/album", methods=['GET','POST'])
@flask_login.login_required
def album():
	if request.method == 'POST':
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		album_name= request.form.get('album_name')
		datetoday = date.today()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums ( album_name, date, user_id) VALUES (%s, %s, %s ) ''' ,(album_name, datetoday, user_id))
		conn.commit()
		albums=getUsersAlbums(user_id)
		for album in albums:
			print(album)
		
		return render_template('album.html', name=flask_login.current_user.id, albums=getUsersAlbums(user_id),base64=base64)
	#The method is GET so we return a  HTML form to create an album
	else:
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		print("Got to GET method of /album")
		return render_template('album.html', albums=getUsersAlbums(user_id))



@app.route("/showphotos", methods=["GET"])
def showallphotos():
	# for each user in db 
	user_id_list = getAllUser_IDS()

	photos = []
	for user_id in user_id_list:
		photos = photos + [getUsersPhotos(user_id)]
	
	return render_template('showphotos.html', AllPhotos=photos, base64=base64)

@app.route("/showalbum", methods=["GET"])
def showallalbums():
	user_id_list = getAllUser_IDS()
	albums = []
	for user_id in user_id_list:
		albums = albums + [  x for x in getUsersAlbums(user_id)  ]
	return render_template('showalbum.html', albums=albums )

@app.route("/showalbum", methods=["POST"])
def selectalbum():
	user_id_list = getAllUser_IDS()
	albums = []
	for user_id in user_id_list:
		albums = albums + [getUsersAlbums(user_id)]

	return render_template('showalbum.html', albums=albums )

@app.route("/show1album/<album_name>", methods=['GET', 'POST'])
def show1album(album_name):
	if request.method == "GET":
		print("ablum name: ", album_name)
		photo = getAlbumsPhotos(album_name)
		return render_template ('show1album.html', album_name=album_name, photos=photo, base64=base64)

@app.route('/errorsameuser')
def sameuser():
		return render_template('errorsameuser.html')	

@app.route("/displayphoto/<photo_id>", methods=['GET', 'POST'])
def displayphoto(photo_id):
	photos = getOnePhotoInfo(photo_id)
	print(" PROCESSING FUNCTION ")
	comments = getCommentsOnPhotos(photo_id)
	if (flask_login.current_user.is_authenticated):
		user_email = flask_login.current_user.id
		user_id = getUserIdFromEmail(user_email)
	else:
		user_id = None

	for comment in comments:
			if comment[0] == None:
				comment[0] = "anonymous"
			else:
				comment[0] = getUserEmailFromUser_Id(comment[0])

	if request.method == 'POST':
		datetoday = date.today()
		commentText= request.form.get('comment')
		print("this is the comment:", commentText)
		if request.form['submit_button'] == 'Like':
			if (flask_login.current_user.is_authenticated):
				insertLike(user_id, photo_id)
		#if request.form['submit_button'] == 'Like':
		#	insertLike(user_id, photo_id)
		# check if user id on photo matches user id for comment if so no execute else 
		if (user_id == getUseridfromphoto(photo_id)[0]):
			return render_template('errorsameuser.html', message="You can not comment on your own photos", photo_info = photos, base64=base64)

		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Comments ( user_id, photo_id, text, date) VALUES (%s, %s, %s, %s ) ''' ,(user_id, photo_id, commentText, datetoday))
		conn.commit()
		return render_template('displayphoto.html', user_like_list = getUserLikeListFor1Photo(photo_id), num_likes= getLikesCountFor1Photo(photo_id)[0], comments=comments , photo_info = photos, base64=base64)

	return render_template('displayphoto.html', user_like_list = getUserLikeListFor1Photo(photo_id), num_likes= getLikesCountFor1Photo(photo_id)[0], comments=comments , photo_info = photos, base64=base64)

def getMatchingComment(comment_text):
	print(" this is comment_text in getMatchingCOmment ", comment_text)
	print(" this is comment_text in getMatchingCOmment ", comment_text)
	cursor = conn.cursor()
	#												HOW TO GET CORRECT EXACT MATCH TEXT?
	cursor.execute('''SELECT user_id, text FROM Comments WHERE text LIKE '%{0}%' ORDER BY user_id desc'''.format(comment_text))
	records = cursor.fetchall()
	print(" this is records: ", records)
	# all user ids in list form
	records_list = [ [x[0], x[1]] for x in records]
	return records_list

@app.route ("/searchcomments", methods=['GET', 'POST'])
def searchcomments():
	if request.method=='POST':
		comment_text= request.form.get('comment')
		matching_comments = getMatchingComment(comment_text)
		print("these are matching comments: ", matching_comments)
		return render_template('searchcomments.html', comments=matching_comments)
	
	return render_template('searchcomments.html') 

@app.route("/friend", methods=['POST'])
@flask_login.login_required
def makefriend():
	user_id1 = getUserIdFromEmail(flask_login.current_user.id)
	user_emails = getAllUser_Emails()
	friend_email = request.form.get('friend_email')
	print(" this is friends email: ", friend_email)
	user_id2 = getUserIdFromEmail (friend_email)
	print(" this is friend's id: ", user_id2)
	cursor = conn.cursor()
	cursor.execute('''INSERT INTO Friends (user_id1, user_id2) VALUES (%s, %s )''', (user_id1, user_id2))
	
	conn.commit()
	friends_ids = getUsersFriends(user_id1)

	friends_emails = []
	for friend_id in friends_ids:
		friends_emails = friends_emails + [getUserEmailFromUser_Id(friend_id)]
	

	return render_template('friend.html', user_emails=user_emails, friends_emails=friends_emails)

@app.route("/friend", methods=['GET'])
@flask_login.login_required
def ListFriends():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	friends_ids = getUsersFriends(user_id)
	user_emails = getAllUser_Emails()
	friends_emails = []
	for friend_id in friends_ids:
		friends_emails = friends_emails + [getUserEmailFromUser_Id(friend_id)]
	
	return render_template('friend.html', user_emails=user_emails, friends_emails=friends_emails)




#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')
	

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
