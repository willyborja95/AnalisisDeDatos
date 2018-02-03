from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Email, Length
from wtforms import StringField, PasswordField

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=10)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=10)])

class RegisterForm(FlaskForm):
    nombres= StringField('Nombres', validators=[InputRequired(), Length(min=4, max=50)])
    apellidos = StringField('Apellidos', validators=[InputRequired(), Length(min=4, max=50)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=10)])
    email = StringField('Email', validators=[InputRequired(), Email(message="Email invalido. Porfavor, ingreselo nuevamente"), Length(min=4, max=50)])
    password1 = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=10)])
    password2 = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=10)])
