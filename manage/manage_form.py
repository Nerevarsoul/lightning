#!/usr/bin/env python
# coding: utf-8

from functools import partial

from wtforms import widgets
from wtforms import StringField, PasswordField, SelectField, DateField
from wtforms import TextAreaField, HiddenField, DecimalField
from wtforms.validators import DataRequired, Email, Optional
from flask_wtf.file import FileField
    

from lightning.extension.form_extension import *
from db import *

class NewEmployeeForm(NewModelForm):
    """Create new employee."""

    # need insert star before required label
    MARK = True

    # need insert colon (двоеточие) after label
    COLON = True

    SEQUENCE = [
        "email", "family_name", "name", "patronymic", "telephone_first", 
        "operator_first", "telephone_second", "operator_second",
        "telephone_third", "operator_third", "job_title", "information_url",
         "birth_date", "time_work", "employee_access", "employee_image"
    ]

    # labels for fields
    LABELS = [
        u"E-mail работника", u"Фамилия работника", u"Имя работника",
        u"Отчество работника", u"Первый телефон работника",
        u"Первый оператор работника", u"Второй телефон работника",
        u"Второй оператор работника", u"Третий телефон работника",
        u"Третий оператор работника", u"Должность работника", 
        u"Информационная ссылка работника", u"дата рождения работника",
        u"График работы", u"Доступ", u"Фото"
    ]

    # placeholder for fields
    DESCRIPTIONS = [u"", u"", u"", u"", u"",
                    u"", u"", u"", u"", u"",
                    u"", u"", u"дд.мм.гггг",
                    u"", u"", u"",]

    telephone_first = StringField(validators=[v_length(max=20), v_required()])
    operator_first = SelectField(coerce=unicode)
    telephone_second = StringField(validators=[v_length(max=20)])
    operator_second = SelectField(coerce=unicode)
    telephone_third = StringField(validators=[v_length(max=20)])
    operator_third = SelectField(coerce=unicode)

    job_title = SelectField(coerce=unicode)
    employee_access = SelectField(coerce=unicode)
    employee_image = FileField()

    class Meta(object):

        # overriding default length validator
        length_validator = v_length

        model = Employee

        only = ["email", "family_name", "name", 
            "patronymic", "job_title", 
            "information_url", "birth_date", 
            "time_work", 
        ]

        field_args = {"email": {"widget": widgets.TextInput(),
                               "validators": [v_required()]},
                      "family_name": {"validators": [v_required()]},
                      "name": {"validators": [v_required()]},
                      "patronymic": {"validators": [v_required()]},
                      "information_url": {"widget": widgets.TextInput()},
                      "time_work": {"widget": widgets.TextInput()},
                      "birth_date": {"format": "%d-%m-%Y"},      
                    }

        def __init__(self):
            pass
