from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,BooleanField,TextAreaField,SelectField,IntegerField
from wtforms.validators import DataRequired,ValidationError




class PackageBuildForm(FlaskForm):
	buildid = StringField('Package Build ID',render_kw={'readonly':True},validators=[DataRequired()])
	pkgname = StringField('Package Name',validators=[DataRequired()])
	description = TextAreaField('Description',validators=[DataRequired()])
	osarch = SelectField('OS Architecture',choices=[('32-Bit','32-Bit'),('64-Bit','64-Bit'),('Multi-Arch','Multi-Arch')])
	pkgsourcepath = StringField('Package Source',validators=[DataRequired()])
	patchboolean = BooleanField('Required Patch')
	patchtype = SelectField('Patch Format',choices=[('Current Patch','Current Patch'),('Legacy Patch','Legacy Patch')])
	patchname = StringField('Patch Name')
	removepkg = TextAreaField('Remove Packages')
	install_script = TextAreaField('Install Script')
	submit = SubmitField('Build')
