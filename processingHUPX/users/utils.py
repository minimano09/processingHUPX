import os
from processingHUPX import app, db
import sqlite3

def delete_trash(reqs, username):
    '''
    Deleting the stored data and files when the user delete one of his requests
    :param reqs: a list which contains Request type requests which belongs to the deleted user
    :param username: the username of the deleted user, we want to delete all of his/her requests
    :return: None
    '''
    db_name = "database_" + username
    db_path = os.path.join(app.root_path, 'static', 'databases', db_name)
    conn = sqlite3.connect(db_path + '.db')
    c = conn.cursor()
    for req in reqs:
        table_name = req.table_name
        plot_name = req.img_name
        div_name = req.div_file
        js_name = req.js_file

        db.session.delete(req)

        plot_path = os.path.join(app.root_path, 'static', 'plots', plot_name)
        div_path = os.path.join(app.root_path, 'static', 'bokeh_divs', div_name)
        js_path = os.path.join(app.root_path, 'static', 'bokeh_scripts', js_name)

        try:
            os.remove(div_path)
        except OSError as error:
            print(error)

        try:
            os.remove(js_path)
        except OSError as error:
            print(error)

        try:
            os.remove(plot_path)
        except OSError as error:
            print(error)

        c.execute('''DROP TABLE IF EXISTS {}'''.format(table_name))

        conn.commit()

    c.close()
    conn.close()

    try:
        os.remove(db_path + ".db")
    except OSError as error:
        print(error)

    return None

