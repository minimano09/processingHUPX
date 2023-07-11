from flask_wtf import FlaskForm
from wtforms import StringField, DateField, BooleanField, RadioField, SubmitField
from wtforms.validators import DataRequired, Optional, ValidationError

#name of the checkboxes
CHECKBOX_NAMES = ['Legjobb vételi ár - HU (EUR/MWh)',
                  'Legjobb kínálati ár - HU (EUR/MWh)',
                  'Súlyozott átlagár (EUR/MWh)',
                  'Vásárolt mennyiség (MW)', 'Eladott mennyiség (MW)',
                  'Importált mennyiség (MW)', 'Exportált mennyiség (MW)']

#form for the new requests
class RequestForm(FlaskForm):
    #title of the request
    title = StringField('Cím', validators=[DataRequired(message='Add meg a lekérdezés címét!')])

    #dae of the request creating
    date = DateField('Dátum: ', validators=[DataRequired(message='Kérlek válassz egy dátumot!')], format='%Y-%m-%d', render_kw={'autocomplete': 'off', 'readonly': 'true'})

    #sheet option of the downloaded Excells
    sheet_option = RadioField('Válaszd ki a napi bontást: ', choices=[('hour', 'Órás'), ('quarter', 'Negyedórás')], validators=[DataRequired(message='Válassz egy opciót!')])
    #frequency option for the depicted data
    frequency = RadioField('Ábrázolt időszak hossza: ', choices=[('daily', 'Napi'), ('weekly', 'Heti'), ('monthly', 'Havi')], validators=[DataRequired(message='Válassz egy opciót!')])
    #option only for the monthly frequency
    detail_by_month = RadioField('Havi adatok megjelenítése: ', choices=[('by_day', 'Napi szinten az átlagok megjelenítése'), ('by_168hours', '168 órás heti bontás megjelenítése')], validators=[Optional()])
    #checkbox options
    box1 = BooleanField(CHECKBOX_NAMES[0])
    box2 = BooleanField(CHECKBOX_NAMES[1])
    box3 = BooleanField(CHECKBOX_NAMES[2])
    box4 = BooleanField(CHECKBOX_NAMES[3])
    box5 = BooleanField(CHECKBOX_NAMES[4])
    box6 = BooleanField(CHECKBOX_NAMES[5])
    box7 = BooleanField(CHECKBOX_NAMES[6])
    #submit field
    submit = SubmitField('Lekérés')

    def get_selected_date(self):
        '''
        :return: selected date of the form
        '''
        return self.date.data.strftime('%Y-%m-%d')
        def __init__(self):
            super().__init__(message_dict=self.message_dict)