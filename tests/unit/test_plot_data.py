import pandas as pd

from processingHUPX.hupx_requests import utils as u
import os
from processingHUPX import app

USERNAME = "testuser"
DATE = '2023-04-01'
DB_NAME = "database_testuser.db"
DB_PATH = os.path.join(app.root_path, 'static', 'databases', DB_NAME)
boxes_list = [1, 2, 3]

df_hour_day = u.get_dataframe(DATE, hour=True, day=True)
df_hour_day = u.fill_missing_values(df_hour_day, day=True)
t_name = u.create_table(df_hour_day, USERNAME)
selected_df = u.selecting_columns(boxes_list, 'database_testuser', t_name)

def test_get_plot_hourly_file_exist(client):
    file_name, _, _ = u.get_plot_hourly(selected_df, boxes_list, USERNAME, hour=True, day=True)
    path = os.path.join(app.root_path, 'static', 'plots', file_name)

    assert os.path.isfile(path)

def test_min_max_values(client):

    _, min, max = u.get_plot_hourly(selected_df, boxes_list, USERNAME, hour=True, day=True)

    df_min = selected_df.iloc[:, :3].min().min()
    print(df_min)
    df_max = selected_df.iloc[:, :3].max().max()

    assert df_min == min
    assert df_max == max

def test_bokeh_script_name(client):
    _, min, max = u.get_plot_hourly(selected_df, boxes_list, USERNAME, hour=True, day=True)
    _, div_file = u.create_bokeh_plot(selected_df, USERNAME, "-1-2-3-", 2, min, max,'teszt bokeh')

    path = os.path.join(app.root_path, 'static', 'bokeh_divs', div_file)

    assert os.path.isfile(path)
    assert div_file.startswith(USERNAME)
    assert div_file.endswith('.html')

def test_bokeh_js_name(client):
    _, min, max = u.get_plot_hourly(selected_df, boxes_list, USERNAME, hour=True, day=True)
    js_file, _ = u.create_bokeh_plot(selected_df, USERNAME, "-1-2-3-", 2, min, max,'teszt bokeh')

    path = os.path.join(app.root_path, 'static', 'bokeh_scripts', js_file)

    assert os.path.isfile(path)
    assert js_file.startswith(USERNAME)
    assert js_file.endswith('.js')
