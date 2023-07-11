from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

#creating the object of the application
app = Flask(__name__)
app.app_context().push()

#configuration of the application
app.config['SECRET_KEY'] = 'a0fad06db6594f27d5cf67486b57060a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

#creating the necessary instances
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'users.login' #function name of the route
login_manager.login_message_category = 'info' #bootstrap class - kék figyelmeztető üzit ad

#importing the Blueprints
from processingHUPX.users.routes import users
from processingHUPX.hupx_requests.routes import hupx_requests
from processingHUPX.main.routes import main
from processingHUPX.errors.handlers import errors

#registrating the Blueprints
app.register_blueprint(users)
app.register_blueprint(hupx_requests)
app.register_blueprint(main)
app.register_blueprint(errors)


