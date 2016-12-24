from wtforms import Form, BooleanField, TextField, StringField, RadioField, HiddenField, TextAreaField, validators, ValidationError, FieldList, FormField
from wtforms.widgets import TextArea
from flask_security.forms import RegisterForm
from wtforms.fields.html5 import EmailField

class TagForm(Form):
    legislation_id = HiddenField("Legislation", [validators.Required()])
    key = HiddenField("Key", [validators.Required()])
    values = TextField('Value')

class OptionForm(Form):
    legislation_id = HiddenField("Legislation", [validators.Required()])
    key = HiddenField("Key", [validators.Required()])
    values = RadioField('Value', choices=[])

class RegisterUserForm(RegisterForm):
    name = StringField('Name / username', [validators.Required()])
    email = EmailField('Email', [validators.Required()])