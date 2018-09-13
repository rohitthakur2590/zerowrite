import os
import secrets
from PIL import Image
from flask import render_template, flash, request, redirect, url_for, abort
from sawrword import app, db, mail
from sawrword.models import User, Post, Article
from sawrword.forms import (LoginForm, RegisterForm, UpdateProfileForm, CommandToSendForm,
	                        OutputForm, PostForm, ArticleForm, RequestResetForm, ResetPasswordForm)
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_user,login_required, logout_user, current_user

from lxml.etree import XMLSyntaxError
from lxml.etree import tostring
from xml.etree  import ElementTree as ET
from flask_mail import Message


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))



@app.route('/')
def index():
	return render_template('index.html')

@app.route('/about_us')
def about_us():
	return render_template('about_us.html')

@app.route('/terms')
def terms():
	return render_template('terms.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if form.validate_on_submit():
		#looking for user in database
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			if check_password_hash(user.password, form.password.data):
				login_user(user, remember=form.remember.data)
				return redirect(url_for('dashboard'))
			flash('Invalid username or password!', category='danger')
			return render_template('login.html', form=form)
		flash('User Not registered! Please Sign Up', category='danger')
		return render_template('login.html', form=form)
		#return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'
	return render_template('login.html', form=form)
'''
sha256 will generate 80 characters long password
'''
@app.route('/signup', methods=['GET', 'POST'])
def signup():
 	form = RegisterForm()
 	if form.validate_on_submit():
 	    hash_password = generate_password_hash(form.password.data, method='sha256')
 	    new_user = User(firstname=form.firstname.data,
 			            lastname=form.lastname.data,
 			            email=form.email.data,
 			            password=hash_password)

 	    user = User.query.filter_by(email=form.email.data).first()
 	    if user:
 	        flash('User with this email account already registered', 'success')
 	        return redirect(url_for('signup'))
 	    db.session.add(new_user)
 	    db.session.commit()
 	    flash(f'Sign Up successful for {form.firstname.data}!', 'success')
 	    return render_template('index.html')


 		#return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

 	return render_template('signup.html', form=form)


@app.route('/notepad', methods=['GET', 'POST'])
@login_required
def notepad():
	#form for input notes
	form = CommandToSendForm()
	outputform = OutputForm()

	command = ""

	#parse button_input.xml
	buttons = parse_buttons()
	button_list = sorted(buttons.items())
	if request.method == 'POST' :
		if 'btn_template' in request.form:
			command = read_command_template(request, buttons)
			#set command into command box
			form.command.data = command
		if 'save' in request.form:
			command = request.form['command'].encode('utf-8')

		return render_template('notepad.html',
    		                    command = command,
    		                    buttons=buttons_list,
    		                    form=form,
    		                    output=output.xml,
    		                    outputform=outputform)

	return render_template('notepad.html', form=form,  outputform=outputform)

def parse_buttons():
	XMLtree = ET.parse('button_template/button_config.xml')
	root = XMLtree.getroot()
	button = {}
	for button in root.findall('button'):
		title = button.find('title')
		button[0] = render_template
	return button

@app.route('/dashboard')
@login_required
def dashboard():
	return render_template('dashboard.html', name=current_user.firstname)


@app.route('/profile')
@login_required
def profile():
	form = UpdateProfileForm()
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('profile.html', name=current_user.firstname, image_file=img_file, form=form)

def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex+ f_ext
	picture_path = os.path.join(app.root_path, 'static/display_pics', picture_fn)

	output_size = (200, 200)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(picture_path)

	return picture_fn


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = UpdateProfileForm()
	if form.validate_on_submit():
		if form.picture.data:
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file

		current_user.firstname = form.firstname.data
		current_user.lastname = form.lastname.data
		current_user.username = form.username.data
		current_user.email= form.email.data
		db.session.commit()
		flash('Profile Updated Successfully', 'success')
		return redirect(url_for('profile'))
	elif request.method == 'GET':
		form.firstname.data = current_user.firstname
		form.lastname.data = current_user.lastname
		form.username.data = current_user.username
		form.email.data = current_user.email
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('edit_profile.html', name=current_user.firstname, image_file=img_file, form=form)



@app.route('/my_blog', methods=['GET', 'POST'])
@login_required
def my_blog():
	form = PostForm()

	if form.validate_on_submit():
		post= Post(title=form.title.data, content=form.content.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Your post has been created!', category='success')
		return redirect(url_for('profile'))
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('my_blog.html', image_file=img_file, form=form, legend = 'Create Post')

@app.route('/my_article', methods=['GET', 'POST'])
@login_required
def my_article():
	form = ArticleForm()

	if form.validate_on_submit():
		article= Article(title=form.title.data, content=form.content.data, author=current_user)
		db.session.add(article)
		db.session.commit()
		flash('Your Article has been published!', category='success')
		return redirect(url_for('profile'))
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('my_article.html', image_file=img_file, form=form, legend = 'Create Article')

@app.route("/<int:post_id>")
def post(post_id):
	post =Post.query.get_or_404(post_id)
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('post.html',  image_file=img_file, title=post.title, post=post)

@app.route("/<int:article_id>")
def article(article_id):
	article =Article.query.get_or_404(article_id)
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('article.html',  image_file=img_file, title=article.title, article=article)

@app.route("/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
	post =Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.title = form.title.data
		post.content = form.content.data
		db.session.commit()
		flash('Post updated successfully!', category='success')
		return redirect(url_for('post', post_id = post.id))
	elif request.method == 'GET':
		form.title.data =post.title
		form.content.data = post.content
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('update_post.html', image_file=img_file, form=form,
		legend = 'Update Post')


@app.route("/<int:article_id>/update", methods=['GET', 'POST'])
@login_required
def update_article(article_id):
	article =Article.query.get_or_404(article_id)
	if article.author != current_user:
		abort(403)
	form = ArticleForm()
	if form.validate_on_submit():
		article.title = form.title.data
		article.content = form.content.data
		db.session.commit()
		flash('Article updated successfully!', category='success')
		return redirect(url_for('article', article_id = article.id))
	elif request.method == 'GET':
		form.title.data =article.title
		form.content.data = article.content
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('update_article.html', image_file=img_file, form=form,
		legend = 'Update Article')

@app.route("/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
	post =Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	db.session.delete(post)
	db.session.commit()
	flash('Post deleted successfully!',category='success')
	return redirect(url_for('blog_home'))

@app.route("/<int:article_id>/delete", methods=['POST'])
@login_required
def delete_article(article_id):
	article =Article.query.get_or_404(article_id)
	if article.author != current_user:
		abort(403)
	db.session.delete(article)
	db.session.commit()
	flash('Article deleted successfully!',category='success')
	return redirect(url_for('blog_home'))



@app.route('/blog_home', methods=['GET', 'POST'])
@login_required
def blog_home():
	page = request.args.get('page', 1, type=int)
	posts= Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('blog_home.html', image_file=img_file, posts=posts)

@app.route('/article_home', methods=['GET', 'POST'])
@login_required
def article_home():
	page = request.args.get('page', 1, type=int)
	articles= Article.query.order_by(Article.date_posted.desc()).paginate(page=page, per_page=5)
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('article_home.html', image_file=img_file, articles=articles)

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route("/user/<string:username>")
def user_post():
	page = request.args.get('page', 1, type=int)
	user = User.query.filter_by(username=username).first_or_404()
	posts= Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
	if posts:
		img_file = url_for('static', filename='display_pics/' + current_user.image_file)
		return render_template('user_post.html', image_file=img_file, posts=posts, user=user)

	articles= Article.query.filter_by(author=user).order_by(Article.date_posted.desc()).paginate(page=page, per_page=5)
	img_file = url_for('static', filename='display_pics/' + current_user.image_file)
	return render_template('user_article.html', image_file=img_file, articles=articles, user=user)


def send_reset_email(user):
	token = user.get_reset_token()
	msg = Message('Password Reset Request', sender='sawrword@gmail.com', recipients=[user.email])

	msg.body = f'''To reset the password click the link below:
	{url_for('reset_token', token=token, _external=True)}
	lINK WILL EXPIRE IN 1 HOUR '''
	mail.send( msg )

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('blog_home'))

	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('Please Check you email for password reset link', category='info')
		return redirect(url_for('login'))
	return render_template('reset_request.html', title= 'Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
	if current_user.is_authenticated:
			return redirect(url_for('blog_home'))

	user = User.verify_reset_token(token)
	if user is None:
		flash('Invalid or Expired Token', category='warning')
		return redirect(url_for('reset_request'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
 		hashed_password = generate_password_hash(form.password.data, method='sha256')
 		user.password = hashed_password
 		db.session.commit()
 		flash('Password updated  successfully for {form.firstname.data}!', 'success')
 		return redirect('login')
	return render_template('reset_token.html', title='Reset Password', form=form)








