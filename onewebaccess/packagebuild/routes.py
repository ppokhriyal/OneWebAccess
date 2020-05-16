from flask import Blueprint,render_template,url_for, flash, redirect, request, abort, session,jsonify
from onewebaccess import app,db, bcrypt
from onewebaccess.home.forms import LoginForm,RegistrationForm
from flask_login import login_user, current_user, logout_user, login_required
from onewebaccess.home.models import User

blue = Blueprint('packagebuild',__name__,template_folder='templates')

@blue.route('/home')
def home():
	return render_template('packagebuild/home.html',title='VXL : Package Builder')

@blue.route('/build')
@login_required
def build():
	return render_template('packagebuild/build.html',title='VXL : Package Builder')