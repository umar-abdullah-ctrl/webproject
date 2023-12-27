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

mysql = MySQL(app)


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
            return render_template('index.html',user=user,login=login)
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
    return render_template('cybersecurity.html',login = session["isloggedin"])

@app.route('/cyberattacks')
def cyberattacks():
    return render_template('courses.html',login = session["isloggedin"])

@app.route('/logout')
def logout():
    session.pop('user_id',None)
    session['isloggedin'] = False 
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if session['isloggedin'] : 

        return render_template('dashboard.html')
    else:
        return "Not Logged In"

@app.route('/news')
def news():
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


    return render_template('news.html')


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

    return render_template('blogs.html', blogs=blogs, user_id = session['user_id'] , prev=prev, next=next,page=page,login = session["isloggedin"])


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

    return render_template('post.html',post=post,name = name )

@app.route('/contact',methods=["GET","POST"])
def contact():
    if not session['isloggedin']:
        return render_template('notloggedin.html')
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
        return render_template("contact.html",login = session["isloggedin"])

@app.route('/myposts/<int:user_id>')
def my_posts(user_id):
    if not session['isloggedin']:
        return render_template('notloggedin.html')
    else:
        cursor = mysql.connection.cursor()
        cursor.execute("Select * from posts where user_id = %s",[user_id])
        posts = cursor.fetchall()
        return render_template('myposts.html',posts = posts,login = session["isloggedin"])

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
    if not session['isloggedin']:
        return render_template('notloggedin.html')
    else:

        youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

        query = "cybersecurity courses"
        max_results = 100

        youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

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
        
        last = math.floor(len(videos) / 16)


        page = request.args.get('page')
        if (not str(page).isnumeric()):
            page = 1
        page = int(page)
        videos = videos[(page)*16:(page-16)*int(16)+ int(16)]
        if page==1:
            prev = "#"
            next = "?page="+ str(page+1)
        elif page==last:
            prev = "?page="+ str(page-1)
            next = "?page="+str(page)
        else:
            prev = "?page="+ str(page-1)
            next = "?page="+ str(page+1)
        print(videos)
        return render_template('youtubecourses.html', videos=videos , next= next ,prev = prev ,user_id=session["user_id"])

@app.route('/details')
def details():
    html = request.args.get('html')
    html = html+".html"
    return render_template(html)
if __name__ == '__main__':
    app.run(debug=True)

