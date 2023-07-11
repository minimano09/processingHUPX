from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from processingHUPX.models import User

#form for the registration
class RegistrationForm(FlaskForm):
    username = StringField('Felhasználónév',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Jelszó', validators=[DataRequired()])
    confirm_password = PasswordField('Jelszó megerősítése',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Regisztrálás')

    def validate_username(self, username):
        '''
        Checking if the username has already existed
        :param username: name of the user
        :return: error if the username is existing, else it returns None
        '''
        user = User.query.filter_by(username=username.data).first()  # ha nincs a db-ben, akkor NaN

        if user:
            raise ValidationError('Ez a felhasználónév már foglalt. Kérlek válassz egy újat.')

    def validate_email(self, email):
        '''
        Checking if the given email has already existed
        :param email: email of the user
        :return: error if the email is existing, else it returns None
        '''
        user = User.query.filter_by(email=email.data).first()  # ha nincs a db-ben, akkor NaN

        if user:
            raise ValidationError('Ez az email cím már használt. Kérlek válassz egy újat.')


#form for the login
class LoginForm(FlaskForm):
    username = StringField('Felhasználónév',
                        validators=[DataRequired()])
    password = PasswordField('Jelszó', validators=[DataRequired()])
    remember = BooleanField('Emlékezz rám')
    submit = SubmitField('Bejelentkezés')