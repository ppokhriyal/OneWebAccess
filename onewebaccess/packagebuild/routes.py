from flask import Blueprint,render_template,url_for, flash, redirect, request, abort, session,jsonify
from onewebaccess import app,db, bcrypt,login_manager
from onewebaccess.packagebuild.forms import PackageBuildForm
from flask_login import login_user, current_user, logout_user, login_required
from onewebaccess.models import PB

blue = Blueprint('packagebuild',__name__,template_folder='templates')

@blue.route('/home')
def home():
	page = request.args.get('page',1,type=int)
	pb = PB.query.paginate(page=page,per_page=10)
	pb_count = len(db.session.query(PB).all())
	return render_template('packagebuild/home.html',title='VXL : Package Builder',pb_count=pb_count)

@blue.route('/new')
@login_required
def build():
	form = PackageBuildForm()
	return render_template('packagebuild/build.html',title='VXL : Package Builder',form=form)