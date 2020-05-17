from flask import Blueprint,render_template,url_for, flash, redirect, request, abort, session,jsonify
from onewebaccess import app,db, bcrypt
from onewebaccess.home.forms import LoginForm,RegistrationForm
from flask_login import login_user, current_user, logout_user, login_required
from onewebaccess.models import User

blue = Blueprint('home',__name__,template_folder='templates')

@blue.route('/')
def home():
	return render_template('home/index.html',title='VXL : OneWebAccess')

@blue.route('/signin',methods=['GET','POST'])
def signin():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password,form.password.data):
			login_user(user)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home.home'))
		else:
			flash('Login Unsuccessful. Please check email or password','danger')

	return render_template('home/login.html',title='VXL : Sign in',form=form)
	
@blue.route('/signup',methods=['GET','POST'])
def signup():
	if current_user.is_authenticated:
		return redirect(url_for('home.home'))

	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password,password_decrypted=form.password.data)
		db.session.add(user)
		db.session.commit()
		flash(f'Your Account has been created! You are now able to login','success')
		return redirect(url_for('home.signin'))
	return render_template('home/register.html',title='Sign up',form=form)


#User Logout
@blue.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home.home'))