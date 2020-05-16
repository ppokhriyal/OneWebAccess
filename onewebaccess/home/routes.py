from flask import Blueprint,render_template,url_for, flash, redirect, request, abort, session,jsonify
from onewebaccess import app
from onewebaccess.home.forms import LoginForm,RegistrationForm

blue = Blueprint('home',__name__,template_folder='templates')

@blue.route('/')
def home():
	form = LoginForm()
	return render_template('home/index.html',title='VXL : OneWebAccess',form=form)

@blue.route('/signup')
def signup():
	form = RegistrationForm()
	return render_template('home/register.html',title='Sign up',form=form)