from flask import Blueprint
from flask import render_template, redirect, flash, url_for, request
from flask_login import login_user, current_user, login_required, logout_user
from processingHUPX import db, bcrypt
from processingHUPX.users.forms import RegistrationForm, LoginForm
from processingHUPX.models import User, Request
import processingHUPX.users.utils as u_utils
import os
from processingHUPX import app

#Blueprint of the users package
users = Blueprint('users', __name__)

@users.route("/register", methods=['GET', 'POST'])
def register():
    '''
    Route of the registration
    :return: If the form is submitted it redirects to the login page,
    else we get the registration form
    '''
    print("valami")
    if current_user.is_authenticated:
        print("beleptem")
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    print(form.username.data)
    if form.validate_on_submit():
        print("Creating user object...")
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, db_name="database_"+form.username.data, is_admin=2)
        db.session.add(user)
        db.session.commit()
        flash(f'A felhasználói fiók elkészült, neki: {form.username.data}!', 'success')
        return redirect(url_for('users.login'))
    print("valami2.0")
    return render_template('register.html', title='Register', form=form)

@users.route("/login", methods=['GET', 'POST'])
def login():
    '''
    Route of the login method
    :return: redirect to the right page with the parameters (if it is necessary)
    '''
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect('next_page') if next_page else redirect(url_for('main.home'))
        else:
            flash('Sikertelen bejelentkezés. Ellenőrizd a felhasználónevet és/vagy jelszót.', 'danger')
    return render_template('login.html', title='Login', form=form)

@users.route("/logout")
def logout():
    '''
    Logging out the current user
    :return: url of the home page
    '''
    logout_user()
    return redirect(url_for('main.home'))

@users.route("/admin/users/<string:username>")
@login_required
def show_users(username):
    '''
    Checking if the current user has admin permission, and giving a list of the other users
    :param username: username of the current user
    :return: redirect to a list of users
    '''
    if current_user.is_admin != 1:
        flash('Nincs jogosultságod ehhez az oldalhoz hozzáférni!', 'danger')
        return redirect(url_for('main.home'))
    page = request.args.get('page', 1, type=int)  # első oldal:1 és oldalszám CSAK int lehet
    user = User.query.filter_by(username=username).first_or_404()

    users = User.query.filter(User.username != username) \
        .order_by(User.username.asc()) \
        .paginate(page=page, per_page=20)
    return render_template('users.html', users=users, user=user)

@users.route('/users/<string:username>/change_admin_role', methods=['POST'])
#@login_required
def change_admin_role(username):
    '''
    Changing the selected user access right
    :param username: username of the current user
    :return: to the same webpage
    '''
    if current_user.is_admin != 1:
        flash('Nincs jogosultságod ehhez az oldalhoz hozzáférni!', 'danger')
        return redirect(url_for('main.home'))
    user = User.query.filter_by(username=username).first_or_404()
    action = request.form['action']
    if action == 'make_admin':
        user.is_admin = 1
    elif action == 'remove_admin':
        user.is_admin = 2
    db.session.commit()
    flash(f"{user.username} számára a felhasználói jogosultság módosult!", 'success')
    return redirect(url_for('users.show_users', username=current_user.username))

@users.route('/users/<string:username>/delete_user', methods=['POST'])
def delete_user(username):
    '''
    Deleting a user with his/her requests and not leaving any garbage
    :param u: username of the user
    :return: the updated user list
    '''
    if current_user.is_admin != 1:
        flash('Nincs jogosultságod ehhez az oldalhoz hozzáférni!', 'danger')
        return redirect(url_for('main.home'))
    user = User.query.filter_by(username=username).first_or_404()
    print(user)
    requests = Request.query.filter_by(owner=user).all()
    print("lekérdezések száma: " + str(len(requests)))
    if len(requests) != 0:
        u_utils.delete_trash(reqs=requests, username=username)

    db.session.delete(user)
    db.session.commit()
    flash(f"{user.username} felhasználói névvel a fiók törlésre került!", 'success')
    return redirect(url_for('users.show_users', username=current_user.username))

@users.route("/user/<string:username>")
def user_requests(username):
    '''
    Giving a list of the users' requests, 5 per page
    :param username: username of the user
    :return: list of the users' requests
    '''
    page = request.args.get('page', 1, type=int)  # első oldal:1 és oldalszám CSAK int lehet
    user = User.query.filter_by(username=username).first_or_404()
    reqs = Request.query.filter_by(owner=user)\
        .order_by(Request.date_requested.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_requests.html', posts=reqs, user=user)

@users.route("/admin/requests/<string:username>")
def show_requests(username):
    '''
    Showing all of the requests from any user in a list
    :param username: username of the user
    :return: all of the requests in a list
    '''
    if current_user.is_admin != 1:
        flash('Nincs jogosultságod az elérni kívánt oldalhoz', 'danger')
        return redirect(url_for('main.home'))
    page = request.args.get('page', 1, type=int)  # első oldal:1 és oldalszám CSAK int lehet
    user = User.query.filter_by(username=username).first_or_404()

    reqs = Request.query \
        .order_by(Request.date_requested.desc()) \
        .paginate(page=page, per_page=5)
    return render_template('user_requests.html', posts=reqs, user=user)

