import os
import datetime
from app import app, api, db
from flask import render_template, request, Response, redirect, session, url_for
from config import Config, articles
from flask_restful import Resource, Api
from models.models import Article, User, Category
from helpers.additional_functions import check_password
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message

s = URLSafeTimedSerializer('Thisisasecret!')
mail = Mail(app)


@app.route('/', methods=["GET"])
def homepage():
    articles = Article.query.all()
    session['hello'] = 'hello world'
    return render_template('blog/index.html', config=Config, articles=articles)


@app.route('/sign-up', methods=['GET'])
def sign_up():
    if session.get('user', False):
        return redirect('/')
    return render_template('blog/signup.html')


@app.route('/user-register', methods=['POST'])
def user_store():
    data = request.form
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        password=data.get('password'),
        bio=data.get('description'),
        created=datetime.datetime.now(),
        admin=0,
        activated=0
    )

    db.session.add(user)
    db.session.commit()

    token = s.dumps(data.get("email"), salt='email-confirm')
    msg = Message('Confirm Email', sender='mariasyad@gmail.com', recipients=["mariasyad@gmail.com"])
    link = url_for('confirm_email', token=token, _external=True)
    msg.html = render_template("/blog/emails/activation.html", link=link)
    mail.send(msg)

    session['user'] = user.serialize
    return redirect("/")


@app.route('/confirm-email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return render_template("blog/notactivated.html")

    user = User.query.filter_by(email=email).first()
    user.activated = True
    db.session.commit()
    return render_template("blog/activated.html")


@app.route('/sign-in', methods=['GET'])
def sign_in():
    if session.get('user', False):
        return redirect('/')
    return render_template('blog/signin.html')


@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(email=request.form.get('username')).first()
    if user:
        if check_password(user.password, request.form.get('password')):
            session['user'] = user.serialize
        else:
            return render_template('blog/signin.html', wrong_data=True, username=request.form.get('username'))
    else:
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            if check_password(user.password, request.form.get('password')):
                session['user'] = user.serialize
            else:
                return render_template('blog/signin.html', wrong_data=True, username=request.form.get('username'))
        else:
            return render_template('blog/signin.html', wrong_data=True, username=request.form.get('username'))
    return redirect('/')


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user')
    return redirect('/')


@app.route('/article/<string:slug>')
def article_details(slug):
    article = Article.query.filter_by(slug=slug).first()
    return render_template('blog/details.html', article=article)


@app.route('/article/create')
def article_create():
    if not session.get('user', False):
        return redirect('/')
    return render_template('blog/article_create.html')


@app.route('/contact-us')
def contact_us():
    return render_template('blog/contact-us.html')


@app.route('/article/store', methods=["POST"])
def article_store():
    if not session.get('user', False):
        return redirect('/')
    data = request.form
    img = request.files['img']
    if img:
        img.save(os.path.join(Config.UPLOAD_PATH, img.filename))
        path = "/" + Config.UPLOAD_PATH + img.filename

    article = Article(
        title=data.get('title'),
        slug=data.get('slug'),
        author_id=1,
        description=data.get('description'),
        short_description=data.get('short_description'),
        img=path
    )

    db.session.add(article)
    db.session.commit()
    return redirect("/")


@app.route('/categories', methods=["GET"])
def show_categories():
    categories = Category.query.all()
    session['hello'] = 'hello world'
    return render_template('blog/categories.html', config=Config, categories=categories)


@app.route('/articles', methods=["GET"])
def show_articles():
    articles = Article.query.all()
    session['hello'] = 'hello world'
    return render_template('blog/articles.html', config=Config, articles=articles)


@app.route('/about', methods=["GET"])
def about_us():
    return render_template('blog/about.html')
