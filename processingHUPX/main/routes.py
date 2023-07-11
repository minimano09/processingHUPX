from flask import Blueprint
from flask import render_template

#Blueprint of the main package
main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    '''
    Route of the home page
    :return: home page of the application
    '''
    return render_template('home.html')
