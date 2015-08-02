#!/usr/bin/env python
# coding: utf-8

import re
import os
from functools import partial
from decimal import InvalidOperation, Decimal
from itertools import izip
from collections import OrderedDict
from abc import ABCMeta, abstractmethod

from flask import abort, redirect, render_template, request, flash
from flask import get_flashed_messages, url_for, jsonify, g
from flask import session, send_from_directory, safe_join
from flask_classy import FlaskView, route
import trafaret as t

from db import *
from lightning.extension.access import access_check
from lightning.extension.image_converter import UIC
from lightning.extension.views_extensions import before, after
from manage_form import ShopSettingsForm


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


AdminWorkImageView.register(app, route_prefix="/admin/", route_base="/")
AdminDocumentsTextsView.register(app, route_prefix="/admin/", route_base="/")
AdminShopSettingsView.register(app, route_prefix="/admin/", route_base="/")
AdminWorkBannerView.register(app, route_prefix="/admin/", route_base="/")
