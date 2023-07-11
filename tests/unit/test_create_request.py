import pytest
from processingHUPX.hupx_requests import utils as u
from processingHUPX import db
from processingHUPX.models import Request
import datetime

def test_one_day_frequency(client):
    date = '2023-04-01'
    result_df = u.get_dataframe(date, hour=True, day=True)

    assert len(result_df) == 24

def test_one_week_frequency(client):
    date = '2023-04-01'
    result_df = u.get_dataframe(date, hour=True, week=True)

    assert result_df['datum'][0].strftime('%Y-%m-%d') == '2023-03-25'
    assert result_df.iloc[-1]['datum'].strftime('%Y-%m-%d') == '2023-04-01'

def test_one_month_frequency(client):
    date = '2023-04-01'
    result_df = u.get_dataframe(date, hour=True)

    assert result_df['datum'][0].strftime('%Y-%m-%d') == '2023-03-01'
    assert result_df.iloc[-1]['datum'].strftime('%Y-%m-%d') == '2023-04-01'

def test_column_names(client):
    date = '2023-04-01'
    result_df = u.create_df(date, hour=True, day=True)

    result_columns = result_df.columns.values.tolist()

    assert result_columns[:9] == u.LEGEND_NAMES

def test_auxiliaries_columns(client):
    date = '2023-04-01'
    result_df = u.create_df(date, hour=True, day=True)
    aux_col_names = ['start', 'end', 'datum', 'ev', 'honap', 'het', 'ora',
                     'perc', 'ora_perc', 'datum_perc', 'ev_het']

    result_columns = result_df.columns.values.tolist()
    assert result_columns[9:] == aux_col_names
    assert len(result_columns) == 20

def test_selected_sheet_is_hour(client):
    date = '2023-04-01'
    result_df = u.create_df(date, hour=True, day=True)

    assert len(result_df) == 24

def test_selected_sheet_is_quarter(client):
    date = '2023-04-01'
    result_df = u.create_df(date, hour=False, day=True)

    assert len(result_df) == 96

DATE = '2023-04-01'
df_day_quarter = u.create_df(DATE, hour=False)

def test_fill_missing_values(client):
    assert 0 < df_day_quarter.isna().sum().sum()

    filled_df = u.fill_missing_values(df_day_quarter)

    assert 0 == filled_df.isna().sum().sum()
