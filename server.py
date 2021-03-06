#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web

from tornado import gen
from tornado.options import define, options, parse_command_line

from sqlite3 import connect

from database_setup import DB_NAME

from db.access import auth, get_tag_access, check_access, check_tag_access

from db.add_entries import add_tag_access, add_tag

from db.structure import get_tag_branch

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/tags/(.*)", TagsHandler),
            (r"/tags", TagsHandler),
            (r"/add_tag", AddTagHandler),
            (r"/add_access", AddAccessHandler)
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/login",
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = connect(DB_NAME)


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        return int(self.get_secure_cookie("user_id"))


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        user_id = tornado.escape.xhtml_escape(self.current_user)
        self.render("templates/index.html", title="Main page",
                    user_id=user_id)

class LoginHandler(BaseHandler):
    def get(self):
        self.render("templates/login.html")

    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")

        user_id = auth(self.db, username, password)

        self.set_secure_cookie("user_id", str(user_id))
        self.redirect("/")

class LogoutHandler(BaseHandler):
    def get(self):
        self.set_secure_cookie("user_id", '')
        self.redirect("/")

class TagsHandler(BaseHandler):
    def get(self, tag_id=None):
        user_id = self.current_user
        recursive = 'full' in self.request.arguments        
        (parent_branch,
         self_tag,
         children_tree) = get_tag_branch(self.db, tag_id, user_id, recursive)

        access_keys, users_access = get_tag_access(self.db, tag_id)

        user_access_keys, user_access = check_tag_access(self.db, tag_id, user_id)

        if self_tag is None:
            self_tag = ['', '', '']
        self.render("templates/tags.html", title="Main page",
                    parent_branch=parent_branch,
                    self_tag=self_tag,
                    children_tree=children_tree,
                    recursive='full' if recursive else '',
                    user_access_keys=user_access_keys,
                    user_access=user_access,
                    users_access=users_access,
                    access_keys=access_keys)

class AddTagHandler(BaseHandler):
    def get(self):
        self.redirect("/tags")

    def post(self):
        name = self.get_argument("name")
        parent_id = self.get_argument("parent_id")

        if parent_id:
            parent_id = int(parent_id)
        else:
            parent_id = None

        add_tag(self.db, name, parent_id)

        if parent_id == None:
            parent_id = ''
        self.redirect("/tags/%s" % parent_id)

class AddAccessHandler(BaseHandler):
    def get(self):
        self.redirect("/tags")

    def post(self):
        keys = ('user_id', 'group_id', 'tag_id', 
            'read', 'write', 'view_log', 'delete_log', 
            'modify_log','view_header')

        fields = {key: self.get_argument(key) for key in keys
                  if key in self.request.arguments }

        add_tag_access(self.db, fields)
        self.redirect("/tags/%s" % fields['tag_id'])


def main():
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
