from flask import Blueprint,render_template,url_for,flash,redirect,request,abort,session,jsonify
from onewebaccess import app,db,bcrypt,celery,login_manager
from onewebaccess.registernode.forms import RegisterNodeForm
from flask_login import login_user, current_user, logout_user, login_required
from onewebaccess.models import User,RegisterHost
import paramiko

blue = Blueprint('registernode',__name__,template_folder='templates',static_folder='static')

@blue.route('/home')
def home():
	reg_node_count = len(db.session.query(RegisterHost).all())

	return render_template('registernode/home.html',title='Register Node',reg_node_count=reg_node_count)

@blue.route('/add',methods=['POST','GET'])
@login_required
def add():
	form = RegisterNodeForm()
	
	with open('/root/.ssh/id_rsa.pub',"r") as f:
		publickey_content = f.read()

	if form.validate_on_submit():
		check_host.delay(str(form.remote_host_ip.data))
		return redirect(url_for('registernode.home'))

	return render_template('registernode/add.html',title='Add Node',form=form,publickey_content=publickey_content)

#Celery Task
@celery.task(name='check_host')
def check_host(ip_address):
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
	client.connect(str(ip_address),timeout=3)
	stdin, stdout, stderr = client.exec_command("hostname")
	cmd_hostname = stdout.read()
	update_db = RegisterHost(ipaddress=ip_address,hostname=cmd_hostname.decode('utf-8').rstrip('\n'),register_host_node=current_user)
	#db.session.add(update_db)
	#db.session.commit()

	return current_user
