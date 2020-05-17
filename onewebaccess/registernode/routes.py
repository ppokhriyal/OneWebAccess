from flask import Blueprint,render_template,url_for, flash, redirect, request, abort, session,jsonify
from onewebaccess import app,db
from onewebaccess.registernode.forms import RegisterNodeForm
from flask_login import login_user, current_user, logout_user, login_required
from onewebaccess.models import RegisterHost
import paramiko

blue = Blueprint('registernode',__name__,template_folder='templates')

@blue.route('/home')
def home():

	return render_template('registernode/home.html',title='Register Node')

@blue.route('/add',methods=['POST','GET'])
@login_required
def add():
	form = RegisterNodeForm()
	
	with open('/root/.ssh/id_rsa.pub',"r") as f:
		publickey_content = f.read()

	if form.validate_on_submit():
		return redirect(url_for('registernode.home'))

	return render_template('registernode/add.html',title='Add Node',form=form,publickey_content=publickey_content)

