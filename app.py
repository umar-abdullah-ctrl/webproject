from flask import Flask, render_template,url_for,redirect,session,flash,request
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired,Email,ValidationError
from datetime import datetime
import bcrypt
from newsapi import NewsApiClient
from flask_mail import Mail 
import os 
from werkzeug.utils import secure_filename
import googleapiclient.discovery
from googleapiclient.discovery import build

import math


API_KEY = "AIzaSyDEBU5x5vjmRrZNjcbgfZZTeJOzcor1nKM"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

app = Flask(__name__)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True ,
    MAIL_USERNAME = '',
    MAIL_PASSWORD = ''
)
mail = Mail(app)
# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '@123'
app.config['MYSQL_DB'] = 'web_project'
app.secret_key = 'secret_key'

charset="utf8mb4",  # Set the character set
use_unicode=True

mysql = MySQL(app)

id = 0
title = "" 

class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(),Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(),Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")

@app.route('/')
def home():
    if session['isloggedin']:
        return render_template("index.html",login = session["isloggedin"],user_id = session['user_id'],admin=session['isadmin'])
    else :
        return render_template("index.html",login = session["isloggedin"])

@app.route('/index')
def index():
    login = session['isloggedin']
    if session['isloggedin'] :
        user_id = int(session['user_id'])
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if user :
            return render_template('index.html',user=user,login=login,user_id = session['user_id'],admin=session['isadmin'])
    else:
        return render_template('index.html',user=None,login=login)

@app.route('/login',methods = ['GET','POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        cursor = mysql.connection.cursor()
        cursor.execute("Select * from users where email = %s", (email,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'),user[3].encode('utf-8')):
            session['user_id'] = user[0]
            session['isloggedin'] = True
            if int(user[0])  == 3 :
                session['isadmin'] = True
            else :
                session['isadmin'] = False 
                

            return redirect(url_for('index'))
        else:
            flash("Login Failed Check your Email and Password")
            return redirect(url_for('login'))

    return render_template("login.html",form = form )


@app.route('/register',methods= ["GET","POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        name = form.name.data 
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))

        mysql.connection.commit()  # Corrected line to commit changes
        cursor.close()

        return redirect(url_for('login'))


    return render_template("register.html",form = form )

@app.route('/cybersecurity')
def cybersecurity():
    if session['isloggedin']:
        return render_template('cybersecurity.html',login = session["isloggedin"],admin = session['isadmin'],user_id = session['user_id'])

    else :
        return render_template('cybersecurity.html',login = session["isloggedin"],admin = session['isadmin'])

@app.route('/cyberattacks')
def cyberattacks():
    if session['isloggedin']:
        return render_template('courses.html',login = session["isloggedin"],admin = session['isadmin'],user_id = session['user_id'])
    else :
        return render_template('courses.html',login = session["isloggedin"],admin = session['isadmin'])


@app.route('/logout')
def logout():
    session.pop('user_id',None)
    session['isloggedin'] = False 
    session['isadmin'] = False 
    return redirect(url_for('index'))

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    if session['isloggedin'] : 

 # Fetch distinct video details from the database
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DISTINCT video_title, video_id FROM courses WHERE user_id = %s", (user_id,))
        results = cursor.fetchall()
        cursor.close()

        video_details_list = []

        # Call the YouTube API to get additional details for each video
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        for result in results:
            video_title, video_id = result

            video_response = youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()

            video_details = video_response['items'][0]['snippet']
            video_details_list.append({'video_title': video_title, 'video_details': video_details})

        # Render the template with video details
        return render_template('dashboard.html', user_id=user_id, video_details_list=video_details_list)
    else:
        return "Not Logged In"

@app.route('/news')
def news():

    cursor = mysql.connection.cursor()
    cursor.execute("select * from news")
    results = cursor.fetchall()
    print(results)
    # Init
    # newsapi = NewsApiClient(api_key='a8fe163509d64ebabe3704f6980cf0cd')

    # # /v2/top-headlines
    # top_headlines = newsapi.get_top_headlines(q='Cyber Security',
    #                                           category='business',  # Keep category if needed
    #                                           language='en',
    #                                           country='us')

    # # /v2/everything
    # all_articles = newsapi.get_everything(q='Cyber Security',
    #                                     sources='bbc-news,the-verge',
    #                                     from_param='2023-11-24',  # Use a date within your plan's allowed range
    #                                     to='2023-12-12',
    #                                     language='en',
    #                                     sort_by='relevancy',
    #                                     page=2)

    # # /v2/top-headlines/sources
    # sources = newsapi.get_sources()


    return render_template('news.html',results = results,login = session['isloggedin'] , admin = session['isadmin'])


@app.route('/blogs')
def blogs():
    cursor = mysql.connection.cursor()
    cursor.execute("Select * from posts")
    blogs = cursor.fetchall()
    last = math.floor(len(blogs) / 1)
    print(blogs)

    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    blogs = blogs[(page-1)*1:(page-1)*int(1)+ int(1)]
    if page==1:
        prev = "#"
        next = "?page="+ str(page+1)
    elif page==last:
        prev = "?page="+ str(page-1)
        next = "?page="+str(page)
    else:
        prev = "?page="+ str(page-1)
        next = "?page="+ str(page+1)

    if session['isloggedin']:
        return render_template('blogs.html', blogs=blogs, user_id = session['user_id'] , prev=prev, next=next,page=page,login = session["isloggedin"],admin = session['isadmin'])
    else :
        return render_template('blogs.html', blogs=blogs, prev=prev, next=next,page=page,login = session["isloggedin"])


@app.route('/createblogs',methods=['GET','POST'])
def createblogs():
    if not session['isloggedin']:
        return render_template('notloggedin.html')

    else : 
        if request.method == 'POST':
            title = request.form.get('title')
            text = request.form.get('text')
            description = request.form.get('description')
            cursor = mysql.connection.cursor()
            f = request.files['file']

            upload_folder = 'static/images/uploads'
            f.save(os.path.join(upload_folder, secure_filename(f.filename)))
            cursor.execute("INSERT INTO  posts (title, content, date , user_id ,description,img_file) VALUES (%s, %s, %s,%s,%s,%s)", (title,text, datetime.now(),session['user_id'],description,f.filename))

            mysql.connection.commit()  # Corrected line to commit changes
            cursor.close()

            return redirect(url_for('blogs'))
        else :
            return render_template('createpost.html',login = session["isloggedin"])

@app.route('/posts/<int:post_id>')
def posts(post_id):
    cursor = mysql.connection.cursor()
    cursor.execute("Select * from posts where sno = %s",[post_id])
    
    post = cursor.fetchone()

    cursor.execute("select user_id from posts where sno = %s ",[post_id])

    user_id = cursor.fetchone()
    id = user_id[0]

    cursor.execute("select name from users where id = %s ",[id])
    username = cursor.fetchone()
    name = username[0]
    print(post)
    if session['isloggedin']:
        return render_template('post.html',post=post,name = name ,login = session['isloggedin'],admin = session['isadmin'],user_id = session['user_id'])
    else :
        return render_template('post.html',post=post,name = name ,login = session['isloggedin'],admin = session['isadmin'])

@app.route('/contact',methods=["GET","POST"])
def contact():
    # if not session['isloggedin']:
    #     return render_template('notloggedin.html')
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        no = request.form.get("number")
        text = request.form.get("text")

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO contact (name, email, phone,msg,date) VALUES (%s, %s, %s,%s,%s)", (name, email, no,text,datetime.now()))
        mysql.connection.commit()  
        mail.send_message("New Message From " + name,sender=email,recipients = ['abdullah.bese21seecs@seecs.edu.pk'],body = text + "\n" + no)
        cursor.close()
        return render_template("contact.html")
    else :
        return render_template("contact.html",login = session["isloggedin"],admin = session['isadmin'])

@app.route('/myposts/<int:user_id>')
def my_posts(user_id):
    if not session['isloggedin']:
        return render_template('notloggedin.html')
    else:
        cursor = mysql.connection.cursor()
        cursor.execute("Select * from posts where user_id = %s",[user_id])
        posts = cursor.fetchall()
        return render_template('myposts.html',posts = posts,login = session["isloggedin"],admin = session['isadmin'],user_id=session['user_id'])

@app.route('/delete/<int:sno>')
def delete(sno):
    print(sno)
    cursor = mysql.connection.cursor()
    cursor.execute("delete from posts where sno = %s",[sno])
    mysql.connection.commit()
    user_id = session['user_id']
    return redirect('/myposts/'+str(user_id))
    
@app.route('/courses')
def courses():
    
    video_id = request.args.get('video_id')
    video_title = request.args.get('video_title')
    if video_id:
        cursor = mysql.connection.cursor()

        # Insert values into the courses table
        cursor.execute("INSERT INTO courses (user_id, video_id, video_title) VALUES (%s, %s, %s)",
                    (session['user_id'], video_id, video_title))

        # Commit the transaction
        mysql.connection.commit()

        # Close the cursor
        cursor.close()
    if not session['isloggedin']:
        return render_template('notloggedin.html')
    else:
        youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

        query = "cybersecurity courses"
        max_results = 100

        search_response = youtube.search().list(
            q=query,
            type="video",
            part="id,snippet",
            maxResults=max_results
        ).execute()

        videos = []

        for search_result in search_response.get("items", []):
            video_id = search_result["id"]["videoId"]
            video_title = search_result["snippet"]["title"]
            videos.append({"title": video_title, "video_id": video_id})
            # video_id = str(video_id)
            # video_title = str(video_title)
            # cursor = mysql.connection.cursor()
            # cursor.execute("INSERT INTO videos (video_title, video_id) VALUES (%s, %s)", (video_title, video_id))
            # mysql.connection.commit()
            # cursor.close()

        videos_per_page = 16  # Assuming you want to display 16 videos per page

        page = request.args.get('page')
        if not str(page).isnumeric():
            page = 1
        page = int(page)

        start_index = (page - 1) * videos_per_page
        end_index = start_index + videos_per_page

        videos_to_display = videos[start_index:end_index]

        last = math.ceil(len(videos) / videos_per_page)

        if page == 1:
            prev = "#"
            next = "?page=" + str(page + 1)
        elif page == last:
            prev = "?page=" + str(page - 1)
            next = "?page=" + str(page)
        else:
            prev = "?page=" + str(page - 1)
            next = "?page=" + str(page + 1)

        return render_template('youtubecourses.html', videos=videos_to_display, next=next, prev=prev, user_id=session["user_id"])
@app.route('/details')
def details():
    html = request.args.get('html')
    html = html+".html"
    return render_template(html)

@app.route('/admin')
def admin():
    return render_template("admin.html")

@app.route('/addnews',methods = ['GET','POST'])
def addnews():
    if request.method == 'POST':
        title = request.form.get("title")
        link = request.form.get("link")
        cursor = mysql.connection.cursor()
        f = request.files['file']

        upload_folder = 'static/images/news'
        f.save(os.path.join(upload_folder, secure_filename(f.filename)))
        cursor.execute("INSERT INTO  news (title, link,img_file) VALUES (%s, %s, %s)", (title,link,f.filename))

        mysql.connection.commit()  # Corrected line to commit changes
        cursor.close()
        return redirect("/addnews")
    return render_template("addnews.html",admin = session['isadmin'],login = session['isloggedin'])

@app.route('/deletenews',methods=['POST','GET'])
def deletenews():
    cursor = mysql.connection.cursor()
    cursor.execute("select * from news")
    results = cursor.fetchall()

    return render_template('deletenews.html',results=results)



@app.route('/newsdelete/<int:id>')
def newsdelete(id):
    print(id)
    cursor = mysql.connection.cursor()
    cursor.execute("delete from news where id = %s",[id])
    mysql.connection.commit()
    return redirect('/deletenews')

if __name__ == '__main__':
    app.run(debug=True)

