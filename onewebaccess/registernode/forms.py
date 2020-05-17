from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField,IntegerField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired,IPAddress


class RegisterNodeForm(FlaskForm):
	remote_host_ip = StringField('Remote Host IP Address',validators=[DataRequired(),IPAddress(message="Please Give Valid IP-Address")])
	pb_submit = SubmitField('Register')