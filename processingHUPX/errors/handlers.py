from flask import Blueprint, render_template

#Blueprint of the errors package
errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def error_404(error):
    '''
    Route for the 404 error
    :param error: type of the error
    :return: template of this error
    '''
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(403)
def error_403(error):
    '''
    Route for the 403 error
    :param error: type of the error
    :return: template of this error
    '''
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(500)
def error_500(error):
    '''
    Route for the 500 error
    :param error: type of the error
    :return: template of this error
    '''
    return render_template('errors/500.html'), 500
