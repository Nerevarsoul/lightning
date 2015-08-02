#!/usr/bin/env python
# coding: utf-8

from __future__ import division
import re
import os
from functools import partial
from decimal import InvalidOperation, Decimal
from collections import OrderedDict
from abc import ABCMeta, abstractmethod
from StringIO import StringIO

from flask import abort, redirect, render_template, request, flash, session
from flask import get_flashed_messages, url_for, jsonify, g
from flask import send_from_directory
from flask_classy import FlaskView, route
import trafaret as t
from PIL.Image import open as img_open
from PIL.Image import ANTIALIAS

from db import *
from lightning.extension.access import access_check
from lightning.extension.image_converter import UIC
from lightning.extension.views_extensions import before, after
from manage_form import *


class AdminWorkBannerView(FlaskView):
    """Work with banners."""

    @staticmethod
    def get_banners():
        """Get banners for def banners."""

        banners = g.db_session.query(ShopImage) \
            .filter_by(task="banners") \
            .outerjoin(ShopImage.image) \
            .options(joinedload(ShopImage.image)) \
            .order_by(Image.comment.desc()) \
            .all()

        attributes = ("effect", "font_type", "font_color", "font_size")
        for banner in banners: 
            [setattr(banner, attributes[pos], value)
                for pos, value in enumerate(banner.image.comment.split(u":")[1:])]   
    
        g.banners = OrderedDict(((unicode(banner.id), banner) for banner in banners))

    @staticmethod
    def get_banner_by_id(banner_id=None):
        """Get banner by id."""

        banner_id = request.form["banner_id"]

        banner = g.db_session.query(ShopImage)\
            .filter_by(id=banner_id) \
            .outerjoin(ShopImage.image) \
            .options(joinedload(ShopImage.image))

        msg = ("AdminWorkBannerView:get_banner_by_id: "
                "banner with id = {}")
        g.banner = get_one(banner, msg.format(banner_id))

    @access_check("admin")
    @before(get_banners)
    def banners(self):
        """Table for banners."""

        return render_template("a_banners.html")

    @access_check("admin", u"запись")
    @route("/post_banner/", methods=["POST"])
    def post_banner(self):
        '''Adding new banner'''

        image = request.files.get("file")
        allow_format = [u"jpg", u"jpeg"]
        img_format = image.filename.lower().split(u".")[-1]
        if img_format not in allow_format:
            msg = ("AdminWorkBannerView:post_banner"
               "unexpected format {}")
            app.logger.error(msg.format(slugify_ru(img_format)))
            return abort(404)
        path="shop_img"
        filename = safe_join(path, image.filename)
        shop_img_path = os.path.join(app.config["MEDIA_DIR"], filename)

        i = 1
        while os.path.exists(shop_img_path):
            image.filename = image.filename.split(".")
            image.filename = u".".join((image.filename[0] + str(i), 
                image.filename[1]))
            filename = safe_join(path, image.filename)
            shop_img_path = os.path.join(app.config["MEDIA_DIR"], filename)
            i += 1

        image.save(shop_img_path, buffer_size=1638400)

        shop_img = ShopImage("banners")
        shop_img.image = Image(file_name=image.filename, 
            description="", path=path) 

        g.db_session.add(shop_img)

        g.db_session.flush()

        shop_img.image.comment = u":".join((str(shop_img.id).zfill(5), 
            "", "", "", ""))

        g.db_session.commit()

        return redirect(url_for("AdminWorkBannerView:banners"))

    @access_check("admin", u"запись")
    @before(get_banner_by_id)
    @route("/delete_banner/", methods=["POST"])
    def delete_banner(self):
        """Delete banner."""

        try:
            os.remove(os.path.join(app.config["MEDIA_DIR"], 
                g.banner.image.path, g.banner.image.file_name))
            g.db_session.delete(g.banner)
            g.db_session.commit()
            return jsonify(status=1)

        except BaseException, e:
            msg = ("AdminWorkBannerView:delete_banner"
                "error {}")
            app.logger.error(msg.format(e))
            return abort(404)
        
        return jsonify(status=0)

    @access_check("admin", u"запись")
    @before(get_banners)
    @route("/edit_banner/", methods=["POST"])
    def edit_banner(self):
        """Edit banner."""

        change_banner = set()

        # check POST data and set new values
        for key, val in request.form.iteritems():

            if not "##" in key:
                continue

            banner_id, field = key.split("##")
            banner = g.banners[banner_id]
            
            if field == "name":
                if banner.image.description != val:
                    banner.image.description = val
            else:
                if getattr(banner, field) != val:
                    setattr(banner, field, val)
                    change_banner.add(banner_id)

        for i in change_banner:
            banner = g.banners[i]
            attributes = ["effect", "font_type", "font_color", "font_size"]
            comment = [getattr(banner, attr)
               for attr in attributes]
            comment.insert(0, banner.image.comment.split(u":")[0])
            banner.image.comment = u":".join(comment)

        g.db_session.commit()

        return redirect(url_for("AdminWorkBannerView:banners"))

    @access_check("admin", u"запись")
    @before(get_banners)
    @route("/change_order/", methods=["POST"])
    def change_order(self):
        """Up and down button."""
        
        if request.form["banner_id"].isdigit() and\
        request.form["banner_goal_id"].isdigit():
            banner = g.banners[request.form["banner_id"]]
            banner_goal = g.banners[request.form["banner_goal_id"]]

            comment = banner.image.comment.split(u":")
            comment_goal = banner_goal.image.comment.split(u":")
            comment[0], comment_goal[0] = comment_goal[0], comment[0]
            banner.image.comment = u":".join(comment)
            banner_goal.image.comment = u":".join(comment_goal)

            g.db_session.commit()
            return jsonify(status=1)

        return jsonify(status=0)


class AdminWorkEmployeeView(FlaskView):

    @staticmethod
    def get_employee():
        """Get employee."""

        employees = g.db_session.query(Employee) \
            .filter(Employee.job_title!=u"администратор") \
            .order_by(Employee.id) \
            .outerjoin(Employee.image) \
            .options(subqueryload(Employee.image)) \
            .outerjoin(Employee.access) \
            .options(subqueryload(Employee.access)) \
            .outerjoin(Employee.telephone) \
            .options(subqueryload(Employee.telephone))

        g.employees = OrderedDict(((unicode(employee.id), employee)
                                    for employee in employees))

    @staticmethod
    def add_image_data(*args, **kwargs):
        """Add image data to employee objects."""

        # add image data to employee obj
        for employee in g.employees.values():
            employee.image_data = None
            if employee.image:
                image_obj = employee.image[0]
                employee.image_data = {
                    "url": url_for(
                        "media", path_to_file=image_obj.path,
                        file_name=image_obj.file_name + "_medium.jpg"),
                    "alt": image_obj.alt
                }

    @staticmethod
    def get_choices(*args, **kwargs):
        """Get choices for form."""

        employees = g.db_session.query(Employee)
        job_titles = set((employee.job_title, employee.job_title)
                          for employee in employees.all())

        g.count_manage = employees.filter_by(job_title=u"менеджер").count()                        
        g.count_manage += employees \
            .filter_by(job_title=u"главный менеджер").count()

        operators = g.db_session.query(Operator).all()
        g.operators = {operator.name: operator for operator in operators}
        operators = [(operator.name, operator.name)
                     for operator in operators]

        all_access = db_session.query(Access).all()
        g.all_access = {u"{} {}".format(access.app_access, 
                                        access.access_level):
                                        access for access in all_access}
        all_access = [(u"{} {}".format(access.app_access, access.access_level), 
                        u"{} {}".format(access.app_access, 
                                        access.access_level))
                                        for access in all_access]
        all_access.insert(0, (u'', u''))

        g.choices = {
            "operator_first": operators,
            "operator_second": operators,
            "operator_third": operators,
            "job_title": job_titles,
            "employee_access": all_access,
        }

    @staticmethod
    def get_employee_by_id(employee_id=None, **kwargs):
        """Get employee by id."""

        if not employee_id:
            employee_id = request.form["employee_id"]

        if employee_id != "new":
            employee = g.db_session.query(Employee)\
                .filter_by(id=employee_id)\
                .outerjoin(Employee.image) \
                .options(subqueryload(Employee.image)) \
                .outerjoin(Employee.access) \
                .options(subqueryload(Employee.access)) \
                .outerjoin(Employee.telephone) \
                .options(subqueryload(Employee.telephone))

            msg = ("AdminWorkEmployeeView:get_employee_by_id: "
                    "employee with id = {}")
            g.employee = get_one(employee, msg.format(employee_id))
        else:
            g.employee = Employee("name", "family", "patronymic")

    @staticmethod
    def fill_employee_form(*args, **kwargs):
        """Fill employee form for change and view employee."""

        g.employee.employee_image = ""

        if g.employee.birth_date:
            g.employee.birth_date = g.employee.birth_date.strftime(u"%d-%m-%Y")

        if g.employee.access:
            g.employee.employee_access = u"{} {}".format(
                                            g.employee.access[0].app_access, 
                                            g.employee.access[0].access_level)

        equivalent = {0: "first", 1: "second", 2: "third"}
        for pos, telephone in enumerate(g.employee.telephone):
            setattr(g.employee, "telephone_{}".format(equivalent[pos]),
                telephone.number)
            setattr(g.employee, "operator_{}".format(equivalent[pos]),
                telephone.operator.name)

    @access_check("admin")
    @before(get_employee, add_image_data)
    def view_employee(self):
        """Table for view all employees."""

        # table head
        g.table_data = [OrderedDict((
            ("image", u"Скрыть фото"),
            ("name", u"ФИО"),
            ("telephone", u"Телефон"),
            ("job_title", u"Должность"),
            ("access", u"Доступ"),
            ("access_level", u"Уровень"),
            ("operation", u"Операции")
        ))] 

        # url for buttons
        view_url = partial(url_for, 
                            endpoint="AdminWorkEmployeeView:view_one_employee")
        change_url = partial(url_for, 
                            endpoint="AdminWorkEmployeeView:change_employee")

        # table body
        g.table_data += [
                {"image": "-",
                "name": "-",
                "telephone": "-",
                "job_title": "-",
                "access": "-",
                "access_level": "-",
                "operation": (
                    {"url": url_for("AdminWorkEmployeeView:create_employee"),
                     "text": u"Добавить"},)
        }]

        if g.employees:

            g.table_data += [
                {"class": employee.id,
                "image": employee.image_data,
                "name": u"{} {} {}".format(employee.family_name, 
                                           employee.name, 
                                           employee.patronymic),
                "telephone": ' '.join([telephone.number \
                                       for telephone in employee.telephone]),
                "job_title": employee.job_title,
                "access": employee.access[0].app_access \
                          if employee.access else "",
                "access_level": employee.access[0].access_level
                                if employee.access else "",
                "operation": (
                    {"url": view_url(employee_id=employee.id),
                      "text": u"Просмотреть"},
                    {"url": change_url(employee_id=employee.id),
                      "text": u"Изменить"},
                    {"url": url_for("AdminWorkEmployeeView:delete_employee"),
                      "text": u"Удалить",
                      "class": "delete"},)}
                for employee in g.employees.values()]

        return render_template("a_employees.html", table_data=g.table_data)

    @access_check("admin")
    @before(get_employee_by_id, get_choices, fill_employee_form)
    @route("/view_one_employee/<int:employee_id>/")
    def view_one_employee(self, **kwargs):
        """View one employee's data."""

        form = NewEmployeeForm(choices=g.choices, obj=g.employee)
        form.for_view = True

        return render_template("create_employee.html", form=form)

    @access_check("admin")
    @before(get_choices)
    def create_employee(self):
        """Interface to create employee."""

        form = NewEmployeeForm(choices=g.choices)
        form.action = url_for("AdminWorkEmployeeView:post_create_employee", 
            employee_id="new")
        form.enctype = "multipart/form-data"

        return render_template("create_employee.html", form=form)

    @access_check("admin")
    @before(get_employee_by_id, get_choices, fill_employee_form)
    @route("/change_employee/<employee_id>/")
    def change_employee(self, **kwargs):
        """Change employee's data."""

        form = NewEmployeeForm(choices=g.choices, obj=g.employee)
        form.action = url_for("AdminWorkEmployeeView:post_create_employee", 
                               employee_id=g.employee.id)
        form.enctype = "multipart/form-data"
        form.for_change = True

        return render_template("create_employee.html", form=form)

    @access_check("admin", u"запись")
    @before(get_choices, get_employee_by_id)
    @route("/post_create_employee/<employee_id>/", methods=["POST"])
    def post_create_employee(self, **kwargs):
        """Create employee."""

        # save employee data
        form = NewEmployeeForm(request.form, choices=g.choices)

        if form.validate():

            form.populate_obj(g.employee)

            # add new phone numbers
            equivalent = {0: "first", 1: "second", 2: "third"}
            amount_tepephone = len(g.employee.telephone)
            for pos in equivalent:
                telephone_code = "telephone_{}".format(equivalent[pos])
                operator_code = "operator_{}".format(equivalent[pos])
                telephone_number = request.form.get(telephone_code)
                operator_name = request.form.get(operator_code)
                if telephone_number: 
                    telephone_obj = Telephone(number=telephone_number)
                    telephone_obj.operator = g.operators[operator_name]
                    if pos < amount_tepephone:
                        if telephone_number != g.employee.telephone[pos].number:
                            g.employee.telephone[pos] = telephone_obj
                    else:
                        g.employee.telephone.append(telephone_obj)
                elif pos < amount_tepephone:
                    g.db_session.delete(g.employee.telephone[pos])

            access = request.form.get("employee_access")

            if access:
                g.employee.access = [g.all_access[access]]

            if not g.employee.id:
                g.db_session.add(g.employee)
                g.db_session.flush()
                g.employee.priority = g.employee.id

            manager = (u"менеджер", u"главный менеджер")
            if g.employee.job_title in manager \
                and not g.employee.manager_code:
                g.employee.manager_code = g.count_manage + 1

            image = request.files["employee_image"]
            if image:

                image_file = image.read()
                img = img_open(StringIO(image_file))
                
                allow_format = [u"jpg", u"jpeg"]
                img_format = image.filename.lower().split(u".")[-1]
                if img_format not in allow_format:
                    msg = ("AdminWorkEmployeeView:post_create_employee"
                    "unexpected format {}")
                    app.logger.error(msg.format(slugify_ru(img_format)))
                    return abort(404)

                # resize and save image
                path_img = os.path.join(app.config["MEDIA_DIR"], 
                                                   u"employee_img",
                                                   u"{}{}".format(
                                                    g.employee.family_name,
                                                    g.employee.id)) 
                if not os.path.exists(path_img):
                        os.makedirs(path_img)
                file_name = g.employee.name
                img.save(os.path.join(path_img, file_name + u"_big.jpg"))
                img = img_open(StringIO(image_file))
                old_image_size = img.size
                ratio = old_image_size[0] / old_image_size[1]
                if ratio > 1:
                    new_img_size = (300, int(300/ratio))
                else:
                    new_img_size = (int(300*ratio), 300)
                img = img.resize(new_img_size, ANTIALIAS)
                img.save(os.path.join(path_img, file_name + u"_medium.jpg"))

                g.employee.image = [Image(file_name=file_name, 
                                        path=os.path.join(u"employee_img", 
                                                   u"{}{}".format(
                                                    g.employee.family_name,
                                                    g.employee.id)))]

            g.db_session.commit()

            return redirect(url_for("AdminWorkEmployeeView:view_employee"))

        # return form with errors
        form.enctype = "multipart/form-data"
        return render_template("create_employee.html", form=form)

    @access_check("admin", u"запись")
    @before(get_employee_by_id)
    @route("/delete_employee/", methods=["POST"])
    def delete_employee(self, **kwargs):
        """Delete employee."""

        try:
            if g.employee.image:
                os.remove(os.path.join(app.config["MEDIA_DIR"], 
                    g.employee.image[0].path, 
                    g.employee.image[0].file_name + u"_big.jpg"))
                os.remove(os.path.join(app.config["MEDIA_DIR"], 
                    g.employee.image[0].path, 
                    g.employee.image[0].file_name + u"_medium.jpg"))
                os.rmdir(os.path.join(app.config["MEDIA_DIR"], 
                    g.employee.image[0].path))

        except OSError as e:
            msg = ("AdminWorkEmployeeView:delete_employee"
                "error {}")
            app.logger.error(msg.format(e))

        except BaseException, e:
            msg = ("AdminWorkEmployeeView:delete_employee"
                "error {}")
            app.logger.error(msg.format(e))
            return jsonify(status="error")

        g.db_session.delete(g.employee)
        g.db_session.commit()
        return jsonify(status="success")

AdminWorkImageView.register(app, route_prefix="/admin/", route_base="/")
AdminDocumentsTextsView.register(app, route_prefix="/admin/", route_base="/")
AdminShopSettingsView.register(app, route_prefix="/admin/", route_base="/")
AdminProductsView.register(app, route_prefix="/admin/", route_base="/")
AdminWorkBannerView.register(app, route_prefix="/admin/", route_base="/")
AdminWorkEmployeeView.register(app, route_prefix="/admin/", route_base="/")
