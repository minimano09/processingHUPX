import pytest
from processingHUPX.hupx_requests import utils as u
import os
from processingHUPX import app
import sqlite3

USERNAME = "testuser"
DATE = '2023-04-01'
DB_NAME = "database_testuser.db"
DB_PATH = os.path.join(app.root_path, 'static', 'databases', DB_NAME)
df_for_test = u.get_dataframe(DATE, hour=True)
df_for_test = u.fill_missing_values(df_for_test)

def test_create_table_with_new_database(client):
    new_table_name = u.create_table(df_for_test, USERNAME)

    assert os.path.isfile(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info({})".format(new_table_name))
    results = c.fetchall()
    conn.close()

    assert 0 < len(results)

def test_table_is_existing(client):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
    result = c.fetchone()[0]
    conn.close()

    assert 0 < result

def test_table_names_are_correct(client):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    table_names = [row[0] for row in c.fetchall()]

    prefix = "table_" + USERNAME

    for table_name in table_names:
        assert table_name.startswith(prefix)

    conn.close()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
first_table_name = c.fetchone()[0]
c.close()
conn.close()
print(first_table_name)

def test_table_columns(client):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info({})".format(first_table_name))
    rows = c.fetchall()
    col_names = [row[1] for row in rows]

    c.close()
    conn.close()

    assert col_names == u.DB_COLUMN_NAMES

df_for_test2 = u.get_dataframe(DATE, hour=True, day=True)
df_for_test2 = u.fill_missing_values(df_for_test2)

def test_num_of_rows(client):
    new_table_name2 = u.create_table(df_for_test2, USERNAME)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM {}".format(new_table_name2))
    row_num = c.fetchone()[0]

    c.close()
    conn.close()

    assert 24 == row_num

def test_selecting_columns_names(client):
    selected_boxes = [1,2,3]
    selected_df = u.selecting_columns(selected_boxes, 'database_testuser', first_table_name)

    cols = selected_df.columns.values.tolist()
    list = []
    for i in selected_boxes:
        list.append(u.DB_COLUMN_NAMES[i])
    list = list + u.DB_COLUMN_NAMES[9:]

    assert cols == list

def test_selecting_columns_nums(client):
    selected_boxes = [1, 2, 3]
    selected_df = u.selecting_columns(selected_boxes, 'database_testuser', first_table_name)

    cols = selected_df.columns.values.tolist()

    assert len(cols) == 14

def test_delete_trash(client):
    temp_user = 'userForDelete'
    df_for_delete = u.get_dataframe(DATE, hour=True, day=True)
    df_for_delete = u.fill_missing_values(df_for_delete, day=True)
    table_name = u.create_table(df_for_delete, temp_user)
    df_for_delete = u.selecting_columns([1, 2, 3], 'database_userForDelete', table_name)
    img, min, max = u.get_plot_hourly(df_for_delete, [1, 2, 3], temp_user, hour=True, day=True)
    script, js = u.create_bokeh_plot(df_for_delete, temp_user, "-1-2-3-", 2, min, max, 'test bokeh', hour=True)

    img_path = os.path.join(app.root_path, 'static', 'plots', img)
    script_path = os.path.join(app.root_path, 'static', 'bokeh_divs', script)
    js_path = os.path.join(app.root_path, 'static', 'bokeh_scripts', js)

    u.delete_trash('database_userForDelete', table_name, img, script, js)

    assert not os.path.isfile(img_path)
    assert not os.path.isfile(script_path)
    assert not os.path.isfile(js_path)
