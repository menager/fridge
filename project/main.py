#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import urllib
import jinja2
import time


from webapp2_extras import security
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=["jinja2.ext.autoescape"],
    autoescape = True)



class Item(ndb.Model):
    name = ndb.StringProperty()


class Fridge(ndb.Model):
    name = ndb.StringProperty()
    inList = ndb.StructuredProperty(Item, repeated = True)
    outList = ndb.StructuredProperty(Item, repeated = True)
    password = ndb.StringProperty()
    #fridgeMates = ndb.StructuredProperty(User, repeated = True)

    def addItemIN(self, item):
        if self.hasItemIN(item) == False:
            newItem = Item()
            newItem.name = item
            self.inList.append(newItem)
            self.put()

            if self.hasItemOUT(item) == True:
                self.removeItemOUT(item)

    def removeItemIN(self, item):
        if self.hasItemIN(item) == True:
            self.addItemOUT(item)
            self.inList = [i for i in self.inList if i.name != item]
            self.put()


    def addItemOUT(self, item):
        if self.hasItemOUT(item) == False:
            newItem = Item()
            newItem.name = item
            self.outList.append(newItem)
            self.put()

            if self.hasItemIN(item) == True:
                self.inList = [i for i in self.inList if i.name != item]
                self.put()


    def removeItemOUT(self, item):
        if self.hasItemOUT(item) == True:
            self.outList = [i for i in self.outList if i.name != item]
            self.put()


    def hasItemIN(self, item):
        have = False
        for i in self.inList:
            if item == i.name:
                have = True
        return have

    def hasItemOUT(self, item):
        have = False
        for i in self.outList:
            if item == i.name:
                have = True
        return have


class LoginHandler(webapp2.RequestHandler):
    def get(self):

        currentUser = self.request.cookies.get("userN")
        badLog = False
        badPass = False
        logged = None
        template_values = {

            'badPass': badPass,
            'badLog': badLog,
        }

        template = JINJA_ENVIRONMENT.get_template("login.html")
        self.response.write(template.render(template_values))

    def post(self):
        badLog = False
        badPass = False
        currentUser = self.request.get("userN").lower()
        userN = self.request.get("userN").lower()
        self.response.set_cookie('userN', userN, path = '/')
        currentUser = userN

        password = self.request.get("passW")
        exist = False
        secur = False
        fridgeList = Fridge.query().fetch()

        for i in fridgeList:
            if i.name == userN:
                exist = True
                if i.password == password:
                    secur = True

        if  not currentUser  or not password :
            badLog = True

            template_values = {

                'badLog': badLog,
            }

            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_values))
        elif not exist:

            template_values = {
                'exist':exist,
            }

            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_values))
        elif not secur:
            badPass = True

            template_values = {

                'badPass': badPass,
            }

            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_values))

        else:
            template_values = {
                'currentUser':currentUser,
            }

            template = JINJA_ENVIRONMENT.get_template("FridgeHome.html")
            self.response.write(template.render(template_values))

class newFridgeHandler(webapp2.RequestHandler):
    def get(self):

        template = JINJA_ENVIRONMENT.get_template("newFridge.html")
        self.response.write(template.render())

    def post(self):

        name = str(self.request.get("userN")).lower()
        password = str(self.request.get("passW"))
        nameEmpty = False
        passEmpty = False
        free = True
        created = False
        if name == "" or name == None:
            nameEmpty = True
        if password == "" or password == None:
            passEmpty = True

        if not nameEmpty and not passEmpty:
             userList = Fridge.query().fetch()
             for i in userList:
                 if i.name.lower() == name.lower():
                     free = False

        if free == True and nameEmpty == False and passEmpty == False:
            newUser = Fridge(id = name )
            newUser.name = name
            newUser.password = password
            newUser.put()
            time.sleep(.5)
            created = True

        users = Fridge.query().fetch()
        template_values = {
            'users':users,
            'nameEmpty':nameEmpty,
            'passEmpty': passEmpty,
            'free': free,
            'created': created,
        }


        template = JINJA_ENVIRONMENT.get_template("newFridge.html")
        self.response.write(template.render(template_values))


class FridgeHandler(webapp2.RequestHandler):
    def get(self):
        currentUser = self.request.cookies.get("userN")
        users = Fridge.query().fetch()
        if currentUser == None or "":
            template = JINJA_ENVIRONMENT.get_template("error.html")
            self.response.write(template.render())
        else:
            template_values = {
                'currentUser': currentUser,
                'users':users,
            }

            template = JINJA_ENVIRONMENT.get_template("FridgeHome.html")
            self.response.write(template.render(template_values))

class missingHandler(webapp2.RequestHandler):
    def get(self):
        currentUser = self.request.cookies.get("userN")
        users = Fridge.query().fetch()
        if currentUser == None or "":
            template = JINJA_ENVIRONMENT.get_template("error.html")
            self.response.write(template.render())
        else:
            template_values = {
                'currentUser':currentUser,
                'users':users,

            }
            template = JINJA_ENVIRONMENT.get_template("missing.html")
            self.response.write(template.render(template_values))

    def post(self):
        currentUser = self.request.cookies.get("userN")
        add = self.request.get("add")
        delete = self.request.get("delete")
        users = Fridge.query().fetch()
        itemName = str(self.request.get("item")).lower()
        checked = self.request.get("checked")
        empty = False
        inOutList = False
        error = False
        error2 = False
        if add:
            if itemName == "" or None:
                empty = True
            else:
                for fridge in users:
                    if fridge.name == currentUser:
                        if fridge.hasItemOUT(itemName):
                            inOutList = True
                        else:
                            fridge.addItemOUT(itemName)
        if delete:
            if (itemName == "" or None):
                error = True
            else:
                for fridge in users:
                    if fridge.name == currentUser:
                        if not fridge.hasItemOUT(itemName):
                            error2 = True
                        else:
                            fridge.removeItemOUT(itemName)

        template_values = {
            'currentUser': currentUser,
            'users': users,
            'empty': empty,
            'error':error,
            'error2':error2,
            'inOutList': inOutList,

        }
        template = JINJA_ENVIRONMENT.get_template("missing.html")
        self.response.write(template.render(template_values))




class inHandler(webapp2.RequestHandler):
    def get(self):
        currentUser = self.request.cookies.get("userN")
        users = Fridge.query().fetch()
        if currentUser == None or "":
            template = JINJA_ENVIRONMENT.get_template("error.html")
            self.response.write(template.render())
        else:

            template_values = {
                'currentUser':currentUser,
                'users':users,

            }
            template = JINJA_ENVIRONMENT.get_template("in.html")
            self.response.write(template.render(template_values))

    def post(self):
        currentUser = self.request.cookies.get("userN")
        add = self.request.get("add")
        delete = self.request.get("delete")
        users = Fridge.query().fetch()
        itemName = str(self.request.get("item")).lower()
        checked = self.request.get("checked")
        empty = False
        inInList = False
        error = False
        error2 = False
        if add:
            if itemName == "" or None:
                empty = True
            else:
                for fridge in users:
                    if fridge.name == currentUser:
                        if fridge.hasItemIN(itemName):
                            inInList = True
                        else:
                            fridge.addItemIN(itemName)
        if delete:
            if (itemName == "" or None):
                error = True
            else:
                for fridge in users:
                    if fridge.name == currentUser:
                        if not fridge.hasItemIN(itemName):
                            error2 = True
                        else:
                            fridge.removeItemIN(itemName)

        template_values = {
            'currentUser': currentUser,
            'users': users,
            'empty': empty,
            'error':error,
            'error2': error2,
            'inInList': inInList,

        }
        template = JINJA_ENVIRONMENT.get_template("in.html")
        self.response.write(template.render(template_values))

class logoutHandler(webapp2.RequestHandler):
    def get(self):
        currentUser = self.request.cookies.get("userN")
        yes = None
        no = None
        if currentUser == None or "":
            template = JINJA_ENVIRONMENT.get_template("error.html")
            self.response.write(template.render())
        else:
            template_values = {
                'yes': yes,
                'no': no,
                'currentUser': currentUser,
            }
            template = JINJA_ENVIRONMENT.get_template("logout.html")
            self.response.write(template.render(template_values))

    def post(self):
        currentUser = self.request.cookies.get("userN")
        yesButton = self.request.get("yes")
        noButton = self.request.get("no")
        yes = False
        no = False
        if yesButton:
            if currentUser:
                self.response.delete_cookie(currentUser)
                self.response.delete_cookie("userN")
                yes = True
                currentUser = None
        if noButton:
            no = True
        template_values = {
            'yes': yes,
            'no': no,
            'currentUser': currentUser,
        }
        template = JINJA_ENVIRONMENT.get_template("logout.html")
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', LoginHandler),
    ('/newFridge', newFridgeHandler),
    ('/FridgeHome', FridgeHandler),
    ('/in', inHandler),
    ('/missing', missingHandler),
    ('/logout', logoutHandler),
], debug=True)
