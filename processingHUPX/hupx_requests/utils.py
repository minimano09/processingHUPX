import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from processingHUPX import app
import requests
import io
import os
import sqlite3
import secrets
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, DatetimeTickFormatter, \
    CheckboxButtonGroup, NumeralTickFormatter, Legend
from bokeh.layouts import column
from bokeh.embed import components
from bokeh.palettes import Category10
import sys

URL = "https://hupx.hu/hu/id/market_data/export.xlsx?date=" #The URL of the original datas, where I download them
HEADER_ROW = 2 #in the downloaded Excels the first 2 rows are unnecessary
#names of the columns without the auxiliary variables
COLUMN_NAMES = ['index',
 'intervallum',
 'Legjobb vételi ár - HU (EUR/MWh)',
 'Legjobb kínálati ár - HU (EUR/MWh)',
 'Súlyozott átlagár (EUR/MWh)',
 'Vásárolt mennyiség (MW)',
 'Eladott mennyiség (MW)',
 'Importált mennyiség (MW)',
 'Exportált mennyiség (MW)',
 'Nettó pozíció (MW)']

#names of the columns in the SQLite3 tables
DB_COLUMN_NAMES = [
    'intervallum', 'best_buying_price_EUR_MWh',
    'best_offer_price_EUR_MWh', 'weighted_average_price_EUR_MWh',
    'quantity_purchased_MW', 'quantity_sold_MW',
    'quantity_imported_MW', 'quantity_exported_MW',
    'netto_position_MW', 'starting', 'ending', 'datum',
    'ev', 'honap', 'het', 'ora', 'perc', 'ora_perc', 'datum_perc', 'ev_het'
]

#legend names of the plots
LEGEND_NAMES = [ 'intervallum',
 'Legjobb vételi ár - HU (EUR/MWh)',
 'Legjobb kínálati ár - HU (EUR/MWh)',
 'Súlyozott átlagár (EUR/MWh)',
 'Vásárolt mennyiség (MW)',
 'Eladott mennyiség (MW)',
 'Importált mennyiség (MW)',
 'Exportált mennyiség (MW)',
 'Nettó pozíció (MW)']

#metrics for the hover tools
METRICS = [ 'intervallum',
    'EUR/MWh',
    'EUR/MWh',
    'EUR/MWh',
    'MW',
    'MW',
    'MW',
    'MW',
    'MW'
]

def create_df(date, hour=False, day=False, week=False):
    '''
    Download the necessary datas, concat them into 1 DataFrame, create the auxiliary columns
    and drop the unnecessary ones
    :param date: selected date in the New request form
    :param hour: True if the selected sheet is 'Órás' and False if the selected sheet is 'Negyedórás'
    :param day: True if we want information about the selected day
    :param week: True if we eant the selected date and the previous 1 week
    :return: the created DataFrame
    '''

    date = pd.to_datetime(str(date))
    if day:
        date_before = date
    elif week:
        date_before = date- timedelta(weeks=1)
    else:
        date_before = date - relativedelta(months=1)
    date_before = date_before.strftime('%Y-%m-%d')
    date_range = pd.date_range(date_before, date)

    df_result = pd.DataFrame()

    for d in date_range:
        text = d.strftime("%Y-%m-%d")
        daily = URL + text
        s = requests.get(daily).content
        df_temp = pd.read_excel(io.BytesIO(s), sheet_name="Órák" if hour else "Negyedórák")
        df_temp.columns = df_temp.iloc[HEADER_ROW]
        df_temp = df_temp.drop(labels=[0,1,2], axis=0)
        df_temp.reset_index(inplace = True)
        df_result = pd.concat([df_result, df_temp], axis=0)

    df_result.reset_index(inplace=True)
    df_result = df_result.iloc[:, 2:]
    df_result = df_result.rename(columns={np.nan: 'intervallum'})
    #df_result.to_excel(r'/Users/kovacsanna/Desktop/data_without_plus_cols.xlsx')
    df_result[['start', 'end']] = df_result['intervallum'].str.split('-', expand=True)
    df_result['start'] = pd.to_datetime(df_result['start'], format='%Y-%m-%d %H:%M')
    df_result['end'] = pd.to_datetime(df_result['end'], format='%Y-%m-%d %H:%M')
    df_result['datum'] = df_result['start'].dt.date
    df_result['ev'] = df_result['start'].dt.year
    df_result['honap'] = df_result['datum'].map(lambda x: str(x)[0:4])
    df_result['het'] = df_result['start'].dt.strftime('%W')
    #df_hour['het'] = df_hour['het'] % (df_hour['het'][0])
    df_result['ora'] = df_result['start'].dt.hour
    df_result['perc'] = df_result['start'].dt.minute
    df_result['ora_perc'] = (
        pd.to_datetime(df_result['ora'].astype(str) + ':' + df_result['perc'].astype(str), format='%H:%M')
        .dt.time)
    df_result['datum_perc'] = pd.to_datetime(df_result['datum'].astype(str) + ' ' + df_result['ora_perc'].astype(str),
                                             format='%Y-%m-%d %H:%M')
    df_result['ev_het'] = pd.to_datetime(df_result['ev'].astype(str) + ' ' + df_result['het'].astype(str) + ' 1', format='%Y %W %w')

    #df_result.to_excel(r'/Users/kovacsanna/Desktop/data_with_plus_cols.xlsx')

    df_result = df_result.drop('Súlyozott átlagár az utolsó órában (EUR/MWh)', axis=1)
    df_result = df_result.drop('Vásárolt mennyiség (MWh)', axis=1)
    df_result = df_result.drop('Eladott mennyiség (MWh)', axis=1)

    return df_result

def get_dataframe(date, hour=False, day=False, week=False):
    '''
    According to the selected options, it is calling the create_df function with the right parameters
    :param date: selected date in the New request form
    :param hour: True if the selected sheet is 'Órás' and False if the selected sheet is 'Negyedórás'
    :param day: True if we want information about the selected day
    :param week: True if we eant the selected date and the previous 1 week
    :return: the DataFrame of the request
    '''
    if day:
        if hour:
            df = create_df(date, hour=True, day=True)
        else:
            df = create_df(date, day=True)
    elif week:
        if hour:
            df = create_df(date, hour=True, week=True)
        else:
            df = create_df(date, week=True)
    else:
        if hour:
            df = create_df(date, hour=True)
        else:
            df = create_df(date)

    return df

def fill_missing_values(df, day=False):
    '''
    Filling the missing values of the DataFrame
    :param df: DataFrame of the request
    :param day: if True, we fill with the mean of the whole day, otherwise we fill with the mean of the same 'ora' value
    :return: DataFrame after the preprocessing
    '''
    if day:
        df = df.fillna(df.mean())
    else:
        df['legjobb_veteli_ar_atlag'] = df["Legjobb vételi ár - HU (EUR/MWh)"].groupby(df['ora']).transform('mean')
        df["Legjobb vételi ár - HU (EUR/MWh)"].fillna(df['legjobb_veteli_ar_atlag'], inplace=True)

        df['legjobb_kinalati_ar_atlag'] = df["Legjobb kínálati ár - HU (EUR/MWh)"].groupby(df['ora']).transform('mean')
        df["Legjobb kínálati ár - HU (EUR/MWh)"].fillna(df['legjobb_kinalati_ar_atlag'], inplace=True)

        df['sulyozott_atlagar_atlag'] = df["Súlyozott átlagár (EUR/MWh)"].groupby(df['ora']).transform('mean')
        df["Súlyozott átlagár (EUR/MWh)"].fillna(df['sulyozott_atlagar_atlag'], inplace=True)

        df['vasarolt_mennyiseg_MW_atlag'] = df["Vásárolt mennyiség (MW)"].groupby(df['ora']).transform('mean')
        df["Vásárolt mennyiség (MW)"].fillna(df['vasarolt_mennyiseg_MW_atlag'], inplace=True)

        df['eladott_mennyiseg_MW_atlag'] = df["Eladott mennyiség (MW)"].groupby(df['ora']).transform('mean')
        df["Eladott mennyiség (MW)"].fillna(df['eladott_mennyiseg_MW_atlag'], inplace=True)

        df['importalt_mennyiseg_MW_atlag'] = df["Importált mennyiség (MW)"].groupby(df['ora']).transform('mean')
        df["Importált mennyiség (MW)"].fillna(df['importalt_mennyiseg_MW_atlag'], inplace=True)

        df['exportalt_mennyiseg_MW_atlag'] = df["Exportált mennyiség (MW)"].groupby(df['ora']).transform('mean')
        df["Exportált mennyiség (MW)"].fillna(df['exportalt_mennyiseg_MW_atlag'], inplace=True)

        df['netto_pozicio_MW_atlag'] = df["Nettó pozíció (MW)"].groupby(df['ora']).transform('mean')
        df["Nettó pozíció (MW)"].fillna(df['netto_pozicio_MW_atlag'], inplace=True)

        df = df.iloc[:, :-8]

    return df

def create_table(df, username):
    '''
    Creating a new table for the DataFrame in the right database
    :param df: DataFrame of the request
    :param username: username of the user who owns the request
    :return: unique tablename of the request
    '''
    db_name = "database_" + username
    table_name = "table_" + username + "_" + secrets.token_hex(8)
    db_path = os.path.join(app.root_path, 'static', 'databases', db_name)
    conn = sqlite3.connect(db_path + ".db")
    c = conn.cursor()

    df.columns = DB_COLUMN_NAMES

    while True:
        c.execute('''SELECT name from sqlite_master
                    WHERE type='table' AND name=?''', (table_name,))
        result = c.fetchone()
        if result is None:
            break
        table_name = "table_" + username + "_" + secrets.token_hex(8)

    c.execute('''CREATE TABLE IF NOT EXISTS {} (id number, intervallum TEXT ,
              best_buying_price_EUR_MWh REAL,
              best_offer_price_EUR_MWh REAL,
              weighted_average_price_EUR_MWh REAL,
              quantity_purchased_MW REAL,
              quantity_sold_MW REAL,
              quantity_imported_MW REAL,
              quantity_exported_MW REAL,
              netto_position_MW REAL,
              starting REAL, ending REAL,
              datum REAL, ev INTEGER, honap number, het INTEGER, ora INTEGER, perc INTEGER, ora_perc REAL, datum_perc REAL, ev_het TEXT)'''.format(table_name))
    conn.commit()

    df.to_sql(table_name, conn, if_exists='replace', index=False)

    c.close()
    conn.close()

    return table_name

def selecting_columns(column_list, db_name, table_name):
    '''
    Selecting the necessary columns from the table for the plotting
    :param column_list: indexes for the selected columns
    :param db_name: name of the database
    :param table_name: name of the table
    :return: selected DataFrame from the table
    '''
    col_list = []
    col_names = []
    for i in column_list:
        col_list.append(DB_COLUMN_NAMES[i])
        col_names.append(DB_COLUMN_NAMES[i])

    db_path = os.path.join(app.root_path, 'static', 'databases', db_name)
    conn = sqlite3.connect(db_path + ".db")
    c = conn.cursor()

    # maradék 12-19 oszlop kell még
    col_list = col_list + DB_COLUMN_NAMES[9:]

    c.execute('''
    SELECT {} FROM {}
              '''.format(', '.join(col_list), table_name))

    df_from_db = pd.DataFrame(c.fetchall())
    df_from_db.columns = col_list

    c.close()
    conn.close()

    return df_from_db


def get_plot_hourly(df, column_num, username, hour=False, quarter=False, day=False):
    '''
    Creating a plot where all of the data is represented, no need of aggregation
    :param df: DataFrame with the selected columns
    :param column_num: indexes of the selected columns
    :param username: username to create a unique filename
    :param hour: True if we selected the 'Órás' sheet option
    :param quarter: True if we selected the 'Negyedórás' sheet option
    :param day: True if we selected the 'Napi' frequency option
    :return: unique name of the created plot;
    minimum and maximum values of the DataFrame which represents the y-axis scale
    '''

    plt.rcParams["figure.figsize"] = (30, 15)
    fig, ax = plt.subplots()
    plt.plot(figure=fig)
    x = df['starting']
    x_label = 'Óra' if day else 'Óra:Perc'

    min = sys.float_info.max
    max = sys.float_info.min
    for i in column_num:
        plt.plot(x, df[DB_COLUMN_NAMES[i]], label=COLUMN_NAMES[i+1])
        temp_min = df[DB_COLUMN_NAMES[i]].min()
        temp_max = df[DB_COLUMN_NAMES[i]].max()
        min = min if temp_min >= min else temp_min
        max = max if temp_max <= max else temp_max

    ax.set_ylim((int(min)-50, int(max)+50))

    ax.set_xlabel(x_label)
    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0, pos.width, pos.height*0.85])
    ax.legend(loc='upper center',
              bbox_to_anchor=(0.5, 1.35),
              fontsize=30, ncol=2)

    plt.xticks(fontsize=15)
    plt.yticks(fontsize=20)
    plt.xticks(rotation=90)
    plt.xlabel(x_label, fontsize=25, labelpad=10)
    plt.ylabel('Mennyiség', fontsize=25)
    plt.xticks(x)

    if hour and day:
        freq = 2
    elif (not hour) and day:
        freq = 10
    elif quarter and (not day):
        freq = 6
    else:
        freq = 20
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(freq))

    img_name = username + "_" + secrets.token_hex(8) + '.png'
    img_path = os.path.join(app.root_path, 'static', 'plots', img_name)
    while os.path.isfile(img_path):
        img_name = username + "_" + secrets.token_hex(8) + '.png'
        img_path = os.path.join(app.root_path, 'static', 'plots', img_name)
    fig.savefig(img_path, bbox_inches="tight")

    plt.close()

    return img_name, min, max

def get_plot_daily(df, column_num, username):
    '''
    Creating a plot where the aggregation of the data is based on the date, it plots the mean of the day
    :param df: DataFrame with the selected columns
    :param column_num: indexes of the selected columns
    :param username: username to create the unique file name
    :return: unique name of the created plot;
    minimum and maximum values of the DataFrame which represents the y-axis scale
    '''

    plt.rcParams["figure.figsize"] = (30, 15)
    fig, ax = plt.subplots()
    plt.plot(figure=fig)
    x_label = 'Dátum'

    min = sys.float_info.max
    max = sys.float_info.min
    for i in column_num:
        grouped_col = df.groupby(df['datum'])[DB_COLUMN_NAMES[i]].mean()
        grouped_col.plot(label=COLUMN_NAMES[i+1], ax=ax)
        temp_min = grouped_col.min()
        temp_max = grouped_col.max()
        min = min if temp_min>=min else temp_min
        max = max if temp_max<=max else temp_max


    ax.set_ylim((int(min)-50, int(max)+50))
    ax.set_xlabel(x_label)
    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0, pos.width, pos.height * 0.85])
    ax.legend(loc='upper center',
              bbox_to_anchor=(0.5, 1.35),
              fontsize=30, ncol=2)

    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.xticks(rotation=45)
    plt.xlabel(x_label, fontsize=25,labelpad=10)
    plt.ylabel('Mennyiség', fontsize=25)

    img_name = username + "_" + secrets.token_hex(8) + '.png'
    img_path = os.path.join(app.root_path, 'static', 'plots', img_name)
    while os.path.isfile(img_path):
        img_name = username + "_" + secrets.token_hex(8) + '.png'
        img_path = os.path.join(app.root_path, 'static', 'plots', img_name)
    fig.savefig(img_path, bbox_inches="tight")

    plt.close()

    return img_name, min, max

def get_plot_by168hour(df, column_num, username):
    '''
    Creating a plot where the aggregation of the data is based on the hour of the week,
    it plots the mean of the same hour of the weeks
    :param df: DataFrame with the selected columns
    :param column_num: indexes of the selected columns
    :param username: username to create the unique file name
    :return: unique name of the created plot;
    minimum and maximum values of the DataFrame which represents the y-axis scale
    '''

    df_temp = df
    df_temp['starting'] = pd.to_datetime(df_temp['starting'])
    df_temp['hour_of_week'] = df_temp['starting'].dt.dayofweek*24 + (df_temp['starting'].dt.hour+1)
    plt.rcParams["figure.figsize"] = (30, 15)
    fig, ax = plt.subplots()
    plt.plot(figure=fig)
    x_label = '168 órás intervallum'

    min = sys.float_info.max
    max = sys.float_info.min
    for i in column_num:
        grouped_col = df.groupby(df['hour_of_week'])[DB_COLUMN_NAMES[i]].mean()
        grouped_col.plot(label=COLUMN_NAMES[i+1], ax=ax)
        temp_min = grouped_col.min()
        temp_max = grouped_col.max()
        min = min if temp_min >= min else temp_min
        max = max if temp_max <= max else temp_max


    ax.set_ylim((int(min)-50, int(max)+50))
    ax.set_xlabel(x_label)
    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0, pos.width, pos.height * 0.85])
    ax.legend(loc='upper center',
              bbox_to_anchor=(0.5, 1.35),
              fontsize=30, ncol=2)

    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.xticks(rotation=45)
    plt.xlabel(x_label, fontsize=25, labelpad=10)
    plt.ylabel('Mennyiség', fontsize=25)

    img_name = secrets.token_hex(8) + '.png'
    img_path = os.path.join(app.root_path, 'static', 'plots', img_name)
    while os.path.isfile(img_path):
        img_name = username + "_" + secrets.token_hex(8) + '.png'
        img_path = os.path.join(app.root_path, 'static', 'plots', img_name)
    fig.savefig(img_path, bbox_inches="tight")

    plt.close()

    return img_name, min, max

def delete_trash(db_name, table_name, plot_name, div_name, script_name):
    '''
    Deleting the stored data and files when the user delete one of his requests
    :param db_name: name of the database where the data of the request is stored
    :param table_name: name of the table which contains the datas of the request
    :param plot_name: name of the file which contains the plot
    :param div_name: name of the file which contains the bokeh plot HTML part
    :param script_name: name of the file which contains the bokeh plot JS part
    :return: None
    '''
    plot_path = os.path.join(app.root_path, 'static', 'plots', plot_name)
    div_path = os.path.join(app.root_path, 'static', 'bokeh_divs', div_name)
    script_path = os.path.join(app.root_path, 'static', 'bokeh_scripts', script_name)

    try:
        os.remove(plot_path)
    except OSError as error:
        print(error)

    try:
        os.remove(div_path)
    except OSError as error:
        print(error)

    try:
        os.remove(script_path)
    except OSError as error:
        print(error)

    db_path = os.path.join(app.root_path, 'static', 'databases', db_name)
    conn = sqlite3.connect(db_path + '.db')
    c = conn.cursor()

    c.execute('''DROP TABLE IF EXISTS {}'''.format(table_name))

    conn.commit()
    c.close()
    conn.close()

    return None

def create_bokeh_plot(selected_df, username, boxes, type_of_plot, min_y, max_y, title, hour=False):
    '''
    Creating the bokeh plot for the request based on the selected options
    :param selected_df: the DataFrame which contains the data of the request
    :param username: username for the unique file name generating
    :param boxes: a string which contains the selected checkboxes, separate by '-'
    :param type_of_plot: 1 if aggregate by date; 2 if aggregate by hour or minute;
    3 if aggregate hour of the day
    :param min_y: minimum value of the y-axis
    :param max_y: maximum value of the y-axis
    :param title: title of the plot
    :param hour: True if the selected sheet option is 'Órás'
    :return: an HTML and a JS file which store the parts of the bokeh plot
    '''

    boxes = boxes.strip("-")
    indexes_as_string = boxes.split("-")
    indexes = [int(i) for i in indexes_as_string]
    num_of_boxes = len(indexes)
    df_for_bokeh = selected_df.iloc[:, :num_of_boxes]

    legends_list = [LEGEND_NAMES[i] for i in indexes]
    metrics_list = [METRICS[i] for i in indexes]
    col_names = [DB_COLUMN_NAMES[i] for i in indexes]

    formatter = DatetimeTickFormatter(
        seconds=["%Y-%m-%d %H:%M:%S"],
        minsec=["%Y-%m-%d %H:%M:%S"],
        minutes=["%Y-%m-%d %H:%M"],
        hourmin=["%Y-%m-%d %H:%M"],
        hours=["%Y-%m-%d %H:%M"],
        days=["%Y-%m-%d"],
        months=["%Y-%m"],
        years=["%Y"]
    )

    if type_of_plot==3:
        p = figure(title=title, x_axis_label='Időpont',
                   y_axis_label='Mennyiség', x_axis_type='linear',
                   width=1100, y_range=(min_y-50, max_y+50))
    else:
        p = figure(title=title, x_axis_label='Időpont',
               y_axis_label='Mennyiség', x_axis_type='datetime',
                   width=1100, y_range=(min_y-50, max_y+50))
        p.xaxis.formatter = formatter


    palette = Category10[8]
    colors = palette[:num_of_boxes]

    lines = []

    #create the plot and the hover tool
    if type_of_plot == 1:
        except_col = 'datum'
        df_for_bokeh = df_for_bokeh.join(selected_df['datum'])
        df_for_bokeh['datum'] = pd.to_datetime(df_for_bokeh['datum'], format='%Y-%m-%d')
        df_grouped = df_for_bokeh.groupby(pd.Grouper(key='datum', freq='D')).mean()

        source = ColumnDataSource(df_grouped)
        for i, col in enumerate(df_grouped.columns):
            line = p.line(x='datum', y=col, source=source, line_width=2,
                          color=colors[i], legend_label=legends_list[i])
            lines.append(line)

        for i in range(len(lines)):
            col_name = col_names[i]
            p.add_tools(HoverTool(renderers=[lines[i]], tooltips=[
                ('Időpont: ', '$x{%Y-%m-%d}'),
                (legends_list[i], f'@{col_name}{{0.00}}{metrics_list[i]}')
            ], formatters={'@col_name': 'numeral', '$x': 'datetime'}))
            p.yaxis[0].formatter = NumeralTickFormatter(format='0.00')

    elif type_of_plot == 2:
        if hour:
            except_col = 'starting'
            df_for_bokeh = df_for_bokeh.join(selected_df['starting'])
            df_for_bokeh['starting'] = pd.to_datetime(df_for_bokeh['starting'], format='%Y-%m-%d %H:%M:%S')
            df_grouped = df_for_bokeh.groupby(pd.Grouper(key='starting', freq='H')).mean()

            source = ColumnDataSource(data=df_grouped)
            for i, col in enumerate(df_grouped.columns):
                line = p.line(x='starting', y=col, source=source, line_width=2, color=colors[i], legend_label=legends_list[i])
                lines.append(line)

            for i in range(len(lines)):
                col_name = col_names[i]
                p.add_tools(HoverTool(renderers=[lines[i]], tooltips=[
                    ('Időpont: ', '$x{%Y-%m-%d %H} óra'),
                    (legends_list[i], f'@{col_name}{{0.00}}{metrics_list[i]}')
                ], formatters={'@col_name': 'numeral', '$x': 'datetime'}))
                p.yaxis[0].formatter = NumeralTickFormatter(format='0.00')

        elif not hour:
            except_col = 'starting'
            df_for_bokeh = df_for_bokeh.join(selected_df['starting'])
            print(df_for_bokeh['starting'].values.tolist())
            df_for_bokeh['starting'] = pd.to_datetime(df_for_bokeh['starting'], format='%Y-%m-%d %H:%M:%S')
            df_grouped = df_for_bokeh.groupby(pd.Grouper(key='starting', freq='15Min')).mean()

            source = ColumnDataSource(df_grouped)
            for i, col in enumerate(df_grouped.columns):
                line = p.line(x='starting', y=col, source=source, line_width=2, color=colors[i], legend_label=legends_list[i])
                lines.append(line)

            for i in range(len(lines)):
                col_name = col_names[i]
                p.add_tools(HoverTool(renderers=[lines[i]], tooltips=[
                    ('Időpont: ', '$x{%Y-%m-%d %H:%M} perc'),
                    (legends_list[i], f'@{col_name}{{0.00}}{metrics_list[i]}')
                ], formatters={'@col_name': 'numeral', '$x': 'datetime'}))
                p.yaxis[0].formatter = NumeralTickFormatter(format='0.00')

    elif type_of_plot == 3:
        except_col = 'hour_of_week'
        df_for_bokeh['starting'] = pd.to_datetime(selected_df['starting'])
        df_for_bokeh['hour_of_week'] = df_for_bokeh['starting'].dt.dayofweek * 24 + (df_for_bokeh['starting'].dt.hour + 1)
        df_for_bokeh.drop(columns=['starting'], axis=1, inplace=True)
        df_grouped = df_for_bokeh.groupby('hour_of_week').mean()

        source = ColumnDataSource(df_grouped)
        for i, col in enumerate(df_grouped.columns):
            line = p.line(x='hour_of_week', y=col, source=source,
                          line_width=2, color=colors[i], legend_label=legends_list[i])
            lines.append(line)

        for i in range(len(lines)):
            col_name = col_names[i]
            p.add_tools(HoverTool(renderers=[lines[i]], tooltips=[
                ('Időpont: ', '@hour_of_week{0}. óra'),
                (legends_list[i], f'@{col_name}{{0.00}}{metrics_list[i]}')
            ], formatters={'@col_name': 'numeral', '@hour_of_week': 'numeral'}))
            p.yaxis[0].formatter = NumeralTickFormatter(format='0.00')
            p.xaxis[0].formatter = NumeralTickFormatter(format='0')


    p.add_layout(Legend(), 'right')

    checkbox_group = CheckboxButtonGroup(labels=legends_list, active=list(range(len(df_grouped.columns))))

    columns = [col for col in source.column_names if col != except_col]
    callback = CustomJS(
        args=dict(lines=lines, checkbox_group=checkbox_group,
                  y_range=p.y_range, source=source, columns=columns), code="""
        var active = checkbox_group.active;
        var y_min = null;
        var y_max = null;

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            if (active.includes(i)) {
                line.visible = true;
                var col_name = columns[i];
                var y_data = line.data_source.data[col_name];
                var local_min = Math.min.apply(y_min, y_data);
                var local_max = Math.max.apply(y_max, y_data);
                if (y_min == null || local_min < y_min) {
                    y_min = local_min;
                }
                if (y_max == null || local_max > y_max) {
                    y_max = local_max;
                }
            } else {
                line.visible = false;
            }
        }

        if (y_min != null && y_max != null) {
            y_range.start = y_min-50;
            y_range.end = y_max+50;
        } else {
            // if there are no visible lines, reset the y-range to the default value
            y_range.start = y_range.start;
            y_range.end = y_range.end;
        }
    """)

    checkbox_group.js_on_change('active', callback)
    checkbox_group.margin = (50, 0, 30, 10)
    checkbox_group.sizing_mode = "stretch_width"

    layout = column(checkbox_group, p)


    #saving the bokeh components
    script, div = components(layout)

    script_name = username + "_" + secrets.token_hex(8) + '.js'
    script_path = os.path.join(app.root_path, 'static', 'bokeh_scripts', script_name)
    while os.path.isfile(script_path):
        script_name = username + "_" + secrets.token_hex(8) + '.js'
        script_path = os.path.join(app.root_path, 'static', 'bokeh_scripts', script_name)
    with open(script_path, 'w') as f:
        f.write(script)

    div_name = username + "_" + secrets.token_hex(8) + '.html'
    div_path = os.path.join(app.root_path, 'static', 'bokeh_divs', div_name)
    while os.path.isfile(div_path):
        div_name = username + "_" + secrets.token_hex(8) + '.html'
        div_path = os.path.join(app.root_path, 'static', 'bokeh_divs', div_name)
    with open(div_path, 'w') as f:
        f.write(div)

    return script_name, div_name