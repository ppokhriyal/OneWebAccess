from flask import Blueprint,render_template,url_for,flash,redirect,request,abort,session,jsonify
from onewebaccess import app,db,bcrypt,login_manager
from onewebaccess.registernode.forms import RegisterNodeForm
from flask_login import login_user, current_user, logout_user, login_required
from onewebaccess.models import User,RegisterHost
import paramiko

blue = Blueprint('registernode',__name__,template_folder='templates')

#Global Paramiko variables
global client
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)

@blue.route('/home')
def home():
	page = request.args.get('page',1,type=int)
	regnode = RegisterHost.query.paginate(page=page,per_page=10)
	reg_node_count = len(db.session.query(RegisterHost).all())
	host_ip_status = []
	for i in db.session.query(RegisterHost).all():
		try:
			client.connect(str(i),timeout=1)
			stdin, stdout, stderr = client.exec_command("hostname")
			if stdout.channel.recv_exit_status() != 0:
				host_ip_status.append('Down')
			else:
				host_ip_status.append('Running')
		except Exception as ee:
			host_ip_status.append('Down')

	return render_template('registernode/home.html',title='Register Node',reg_node_count=reg_node_count,regnode=regnode,host_ip_status=host_ip_status)

@blue.route('/add',methods=['POST','GET'])
@login_required
def add():
	form = RegisterNodeForm()
	
	with open('/root/.ssh/id_rsa.pub',"r") as f:
		publickey_content = f.read()
	if form.validate_on_submit():
		try:
			client.connect(str(form.remote_host_ip.data),timeout=1)
		except Exception as ee:
			flash (f'Connection Timeout : {str(form.remote_host_ip.data)}','danger')
			return redirect(url_for('registernode.home'))
		
		stdin, stdout, stderr = client.exec_command("hostname")
		cmd_hostname = stdout.read()
		try:
			update_db = RegisterHost(ipaddress=str(form.remote_host_ip.data),hostname=cmd_hostname.decode('utf-8').rstrip('\n'),register_host_node=current_user)
			db.session.add(update_db)
			db.session.commit()
		except Exception as ee:
			flash (f'Database Update Error : {str(form.remote_host_ip.data)}','danger')
			return redirect(url_for('registernode.home'))

	return render_template('registernode/add.html',title='Add Node',form=form,publickey_content=publickey_content)

