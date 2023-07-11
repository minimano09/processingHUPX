from flask import render_template, flash, url_for, redirect, abort, send_file
from flask_login import login_required, current_user
from processingHUPX.models import Request
from processingHUPX.hupx_requests.forms import RequestForm
from processingHUPX import app, db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
from PIL import Image
import os
import io
import tempfile
import processingHUPX.hupx_requests.utils as r_utils
import requests

from flask import Blueprint

#Blueprint of the hupx_requests package
hupx_requests = Blueprint('hupx_requests', __name__)

@hupx_requests.route("/new_request", methods=['GET', 'POST'])
@login_required
def new_request():
    '''
    Route for creating a new request. With the information from the form, it generate the DataFrame,database table
     and plots.
    :return: route of this page if we did not validate, or the route of the created request
    '''
    form = RequestForm()

    if form.validate_on_submit():
        selected_date = form.get_selected_date()

        sheet = form.sheet_option.data
        freq = form.frequency.data
        freq_by_month = form.detail_by_month.data
        selected_boxes = []

        if form.box1.data: selected_boxes.append(1)
        if form.box2.data: selected_boxes.append(2)
        if form.box3.data: selected_boxes.append(3)
        if form.box4.data: selected_boxes.append(4)
        if form.box5.data: selected_boxes.append(5)
        if form.box6.data: selected_boxes.append(6)
        if form.box7.data: selected_boxes.append(7)
        boxes = "-"
        for i in selected_boxes:
            boxes = boxes + str(i) + "-"
        print(boxes)

        database_name = current_user.db_name
        username = current_user.username
        plot_name = ""
        if sheet == 'hour':
            if freq == 'daily':
                try:
                    df = r_utils.get_dataframe(selected_date, hour=True, day=True)
                except requests.exceptions.ConnectionError as e:
                    return render_template('server_not_found.html')
                df = r_utils.fill_missing_values(df, day=True)

            elif freq == 'weekly':
                try:
                    df = r_utils.get_dataframe(selected_date, hour=True, week=True)
                except requests.exceptions.ConnectionError as e:
                    return render_template('server_not_found.html')
                df = r_utils.fill_missing_values(df)
            else:
                try:
                    df = r_utils.get_dataframe(selected_date, hour=True)
                except requests.exceptions.ConnectionError as e:
                    return render_template('server_not_found.html')
                df = r_utils.fill_missing_values(df)
        else:
            if freq == 'daily':
                try:
                    df = r_utils.get_dataframe(selected_date, day=True)
                except requests.exceptions.ConnectionError as e:
                    return render_template('server_not_found.html')
                df = r_utils.fill_missing_values(df, day=True)

            elif freq == 'weekly':
                try:
                    df = r_utils.get_dataframe(selected_date, week=True)
                except requests.exceptions.ConnectionError as e:
                    return render_template('server_not_found.html')
                df = r_utils.fill_missing_values(df)
            else:
                try:
                    df = r_utils.get_dataframe(selected_date)
                except requests.exceptions.ConnectionError as e:
                    return render_template('server_not_found.html')
                df = r_utils.fill_missing_values(df)

        print(df.columns.values.tolist())

        table_name = r_utils.create_table(df, username)
        selected_df = r_utils.selecting_columns(selected_boxes, database_name, table_name)
        img_path = os.path.join(app.root_path, 'static', 'plots')

        if sheet=='hour':
            if freq=='daily':
                plot_name, min_y, max_y = r_utils.get_plot_hourly(selected_df, selected_boxes, username, hour=True, day=True)
                script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username, boxes=boxes,
                                                              type_of_plot=2, hour=True, min_y=min_y, max_y=max_y, title=form.title.data)
            elif freq=='weekly':
                plot_name, min_y, max_y = r_utils.get_plot_hourly(selected_df, selected_boxes, username, day=True)
                script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username, boxes=boxes,
                                                              type_of_plot=2, hour=True, min_y=min_y, max_y=max_y, title=form.title.data)
            else:
                if freq_by_month=='by_day':
                    plot_name, min_y, max_y = r_utils.get_plot_daily(selected_df, selected_boxes, username)
                    script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username,
                                                                  boxes=boxes, type_of_plot=1, min_y=min_y, max_y=max_y, title=form.title.data)
                else:
                    plot_name, min_y, max_y = r_utils.get_plot_by168hour(selected_df, selected_boxes, username)
                    script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username,
                                                                  boxes=boxes, type_of_plot=3, min_y=min_y, max_y=max_y, title=form.title.data)
        else:
            if freq=='daily':
                plot_name, min_y, max_y = r_utils.get_plot_hourly(selected_df, selected_boxes, username, quarter=True)
                script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username, boxes=boxes,
                                                              type_of_plot=2, hour=False, min_y=min_y, max_y=max_y, title=form.title.data)
            elif freq=='weekly':
                plot_name, min_y, max_y = r_utils.get_plot_hourly(selected_df, selected_boxes, username)
                script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username, boxes=boxes,
                                                              type_of_plot=3, min_y=min_y, max_y=max_y, title=form.title.data)
            else:
                if freq_by_month=='by_day':
                    plot_name, min_y, max_y = r_utils.get_plot_daily(selected_df, selected_boxes, username)
                    script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username,
                                                                  boxes=boxes, type_of_plot=1, min_y=min_y, max_y=max_y, title=form.title.data)
                else:
                    plot_name, min_y, max_y = r_utils.get_plot_by168hour(selected_df, selected_boxes, username)
                    script_name, div_name = r_utils.create_bokeh_plot(selected_df=selected_df, username=username,
                                                                  boxes=boxes, type_of_plot=3, min_y=min_y, max_y=max_y, title=form.title.data)



        req = Request(title=form.title.data, owner=current_user, img_name=plot_name,
                      table_name=table_name, boxes=boxes,
                      js_file=script_name, div_file=div_name)
        db.session.add(req)
        db.session.commit()

        flash('A lekérdezés sikeresen elkészült!', 'success')
        return render_template('req.html', title=req.title, request=req, plot=req.img_name)

    else:
        form_error = 'Javítsd ki az alábbi hibákat.'

    return render_template('new_request.html', title='Request', form=form)

@hupx_requests.route("/post/<int:req_id>")
@login_required
def req(req_id):
    '''
    This page displays only the selected request
    :param req_id: selected request's id
    :return: webpage of the selected request
    '''
    one_req = Request.query.get_or_404(req_id)
    return render_template('req.html', title=one_req.title, request=one_req, plot=one_req.img_name)


@hupx_requests.route("/post/<int:req_id>/delete", methods=['POST'])
@login_required
def delete_request(req_id):
    '''
    Deleting the selected request
    :param req_id: selected request's id
    :return: a message as a receipt and a redirect to the home page
    '''
    req = Request.query.get_or_404(req_id)
    table_name = req.table_name
    plot_name = req.img_name
    db_name = "database_" + str(req.owner.username)
    if req.owner != current_user and current_user.is_admin != 1:
        abort(403)
    db.session.delete(req)
    db.session.commit()

    r_utils.delete_trash(db_name, table_name, plot_name, req.div_file, req.js_file)

    flash('A lekérdezésed törölve lett!', 'success')
    return redirect(url_for('main.home'))

@hupx_requests.route("/post/<int:req_id>/save_png", methods=['GET'])
def save_plot_as_png(req_id):
    '''
    Saving the selected plot to the computer as a PNG
    :param req_id: selected request's id
    :return: a PNG file about the plot
    '''
    req = Request.query.get_or_404(req_id)
    img_name = req.img_name

    path = os.path.join(app.root_path, 'static', 'plots', img_name)

    return send_file(path, mimetype='image/png', download_name=f'{req.title}.png' ,as_attachment=True)

@hupx_requests.route("/post/<int:req_id>/save_pdf", methods=['GET'])
def save_plot_as_pdf(req_id):
    '''
    Saving the selected plot to the computer as a PDF
    :param req_id: selected request's id
    :return: a PDF file about the plot
    '''
    req = Request.query.get_or_404(req_id)
    img_name = req.img_name

    path = os.path.join(app.root_path, 'static', 'plots', img_name)
    img = Image.open(path)

    img = img.transpose(method=Image.ROTATE_90)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
        img.save(f.name)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawImage(f.name, 0, 0, width=letter[0], height=letter[1])
    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    os.unlink(f.name) #töröljük az ideiglenes képet

    return send_file(buffer, mimetype='application/pdf', download_name=f'{req.title}.pdf' ,as_attachment=True)

@hupx_requests.route("/post/<int:req_id>/save_excel", methods=['GET'])
def save_df_as_excel(req_id):
    '''
    Saving the plotted data stored in an Excell
    :param req_id: selected request's id
    :return: an Excell file about the plotted data
    '''
    req = Request.query.get_or_404(req_id)
    db_name = "database_" + str(req.owner.username)
    table_name = req.table_name
    boxes = req.boxes
    cols = [int(num) for num in boxes.split("-") if num]
    col_names = [r_utils.LEGEND_NAMES[i] for i in cols]
    col_names = col_names + ["kezdés", "befejezés", "dátum"]

    df_for_save = r_utils.selecting_columns(cols, db_name, table_name)
    df_for_save = df_for_save.iloc[:,:-8]
    df_for_save.columns = col_names

    excel_buf = io.BytesIO()
    writer = pd.ExcelWriter(excel_buf)
    df_for_save.to_excel(writer, sheet_name='Eredmény')
    writer.save()
    excel_buf.seek(0)

    return send_file(excel_buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name=f'{req.title}.xlsx' ,as_attachment=True)

@hupx_requests.route("/post/<int:req_id>/save_csv", methods=['GET'])
def save_df_as_csv(req_id):
    '''
    Saving the plotted data stored as a CSV
    :param req_id: selected request's id
    :return: a CSV file about the plotted data
    '''
    req = Request.query.get_or_404(req_id)
    db_name = "database_" + str(req.owner.username)
    table_name = req.table_name
    boxes = req.boxes
    cols = [int(num) for num in boxes.split("-") if num]
    col_names = [r_utils.LEGEND_NAMES[i] for i in cols]
    col_names = col_names + ["kezdés", "befejezés", "dátum"]

    df_for_save = r_utils.selecting_columns(cols, db_name, table_name)
    df_for_save = df_for_save.iloc[:, :-8]
    df_for_save.columns = col_names

    csv_bytes = io.BytesIO()
    df_for_save.to_csv(csv_bytes, index=False)

    buffer = io.BytesIO(csv_bytes.getvalue())

    return send_file(buffer, mimetype='text/csv', download_name=f'{req.title}.csv', as_attachment=True)



from bokeh.embed import components, file_html
from bokeh.models import Div
from bokeh.resources import CDN, INLINE
@hupx_requests.route("/post/<int:req_id>/update", methods=['GET', 'POST'])
@login_required
def update_request(req_id):
    '''
    Gettint the necessary components of the bokeh plot and redirect to the url
    where the plot is modifiable
    :param req_id: selected request's id
    :return: the webpage where we can modify the bokeh plot
    '''
    req = Request.query.get_or_404(req_id)
    if req.owner != current_user and current_user.is_admin != 1:
        abort(403)
    js_path = os.path.join(app.root_path, 'static', 'bokeh_scripts', req.js_file)
    div_path = os.path.join(app.root_path, 'static', 'bokeh_divs', req.div_file)

    with open(js_path, 'r') as f:
        script = f.read()

    with open(div_path, 'r') as f:
        div = f.read()

    return render_template('update_request.html', title="Bokeh Plot", script=script, div=div)
