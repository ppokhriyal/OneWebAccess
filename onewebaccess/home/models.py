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
	
	def __repr__(self):
		return f"User('{self.username}')"
