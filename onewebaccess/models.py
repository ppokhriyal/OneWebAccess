from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from onewebaccess import db, login_manager, app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class User(db.Model,UserMixin):
	__bind_key__ = 'users'
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(20),unique=True,nullable=False)
	email = db.Column(db.String(120),unique=True,nullable=False)
	password = db.Column(db.String(60),nullable=False)
	password_decrypted = db.Column(db.String(60),nullable=False)
	reg_node = db.relationship('RegisterHost',backref='register_host_node',lazy=True,cascade='all,delete-orphan')
	pb_info = db.relationship('PB',backref='pb_author',lazy=True,cascade='all,delete-orphan')
	
	def __repr__(self):
		return f"User('{self.username}')"

class PB(db.Model):
	__bind_key__ = 'pb'
	id = db.Column(db.Integer,primary_key=True)
	buildid = db.Column(db.Integer,unique=True,nullable=False)
	pkgname = db.Column(db.String(60),nullable=False)
	description = db.Column(db.Text,nullable=False)
	osarch = db.Column(db.Text,nullable=False)
	date_posted = db.Column(db.DateTime(),nullable=False,default=datetime.now)
	patchname = db.Column(db.String(60))
	md5sum_pkg = db.Column(db.String(50),nullable=False)
	md5sum_patch = db.Column(db.String(50))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class RegisterHost(db.Model):
	__bind_key__ = 'regnode'
	id = db.Column(db.Integer,primary_key=True)
	ipaddress = db.Column(db.String(20),unique=True,nullable=False)
	hostname = db.Column(db.String(20),nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return f"{self.ipaddress}"