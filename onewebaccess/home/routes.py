from flask import Blueprint,render_template,url_for, flash, redirect, request, abort, session,jsonify
from onewebaccess import app

blue = Blueprint('home',__name__,template_folder='templates')

@blue.route('/')
def home():

	return render_template('home/index.html',title='VXL:OneWebAccess')