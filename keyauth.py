import os
import json as jsond  # json
import time  # sleep before exit
import binascii  # hex encoding
from uuid import uuid4  # gen random guid
import platform  # check platform
import subprocess  # needed for mac device
import hmac # signature checksum
import hashlib # signature checksum
from telegram import Update
import requests


class api:

    name = ownerid = secret = version = ""

    def __init__(self, name, ownerid, secret, version):
        if len(ownerid) != 10 and len(secret) != 64:
            print("Go to Manage Applications on dashboard, copy python code, and replace code in main.py with that")
            time.sleep(3)
            os._exit(1)
    
        self.name = name

        self.ownerid = ownerid

        self.secret = secret

        self.version = version
        self.init()

    sessionid = enckey = ""
    initialized = False

    def init(self):
        if self.sessionid != "":
            print("You've already initialized!")
            time.sleep(3)
            os._exit(1)

        sent_key = str(uuid4())[:16]
        
        self.enckey = sent_key + "-" + self.secret
        
        post_data = {
            "type": "init",
            "ver": self.version,
            "enckey": sent_key,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        if response == "KeyAuth_Invalid":
            print("The application doesn't exist")
            time.sleep(3)
            os._exit(1)

        json = jsond.loads(response)

        if json["message"] == "invalidver":
            if json["download"] != "":
                print("New Version Available")
                download_link = json["download"]
                os.system(f"start {download_link}")
                time.sleep(3)
                os._exit(1)
            else:
                print("Invalid Version, Contact owner to add download link to latest app version")
                time.sleep(3)
                os._exit(1)

        if not json["success"]:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

        self.sessionid = json["sessionid"]
        self.initialized = True
        self.__load_app_data(json["appinfo"])

    async def register(self, user, password, license):
        self.checkinit()

        post_data = {
            "type": "register",
            "username": user,
            "pass": password,
            "key": license,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            print("Successfully registered")
            self.__load_user_data(json["info"])
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def upgrade(self, user, license):
        self.checkinit()

        post_data = {
            "type": "upgrade",
            "username": user,
            "key": license,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            print("Successfully upgraded user")
            print("Please restart program and login")
            time.sleep(3)
            os._exit(1)
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    async def login(self, user, password):
        self.checkinit()

        post_data = {
            "type": "login",
            "username": user,
            "pass": password,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            self.__load_user_data(json["info"])
            print("Successfully logged in")
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def license(self, key):
        self.checkinit()

        post_data = {
            "type": "license",
            "key": key,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            self.__load_user_data(json["info"])
            print("Successfully logged in with license")
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def var(self, name):
        self.checkinit()

        post_data = {
            "type": "var",
            "varid": name,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            return json["message"]
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def getvar(self, var_name):
        self.checkinit()

        post_data = {
            "type": "getvar",
            "var": var_name,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }
        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            return json["response"]
        else:
            print(f"NOTE: This is commonly misunderstood. This is for user variables, not the normal variables.\nUse keyauthapp.var(\"{var_name}\") for normal variables");
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def setvar(self, var_name, var_data):
        self.checkinit()

        post_data = {
            "type": "setvar",
            "var": var_name,
            "data": var_data,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }
        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            return True
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def ban(self):
        self.checkinit()

        post_data = {
            "type": "ban",
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }
        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            return True
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def file(self, fileid):
        self.checkinit()

        post_data = {
            "type": "file",
            "fileid": fileid,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if not json["success"]:
            print(json["message"])
            time.sleep(3)
            os._exit(1)
        return binascii.unhexlify(json["contents"])

    def webhook(self, webid, param, body = "", conttype = ""):
        self.checkinit()

        post_data = {
            "type": "webhook",
            "webid": webid,
            "params": param,
            "body": body,
            "conttype": conttype,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            return json["message"]
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)

    def check(self):
        self.checkinit()

        post_data = {
            "type": "check",
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }
        response = self.__do_request(post_data)

        json = jsond.loads(response)
        if json["success"]:
            return True
        else:
            return False

    def checkblacklist(self):
        self.checkinit()

        post_data = {
            "type": "checkblacklist",
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }
        response = self.__do_request(post_data)

        json = jsond.loads(response)
        if json["success"]:
            return True
        else:
            return False

    def log(self, message):
        self.checkinit()

        post_data = {
            "type": "log",
            "pcuser": os.getenv('username'),
            "message": message,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        self.__do_request(post_data)

    def fetchOnline(self):
        self.checkinit()

        post_data = {
            "type": "fetchOnline",
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            if len(json["users"]) == 0:
                return None
            else:
                return json["users"]
        else:
            return None

    def chatGet(self, channel):
        self.checkinit()

        post_data = {
            "type": "chatget",
            "channel": channel,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            return json["messages"]
        else:
            return None

    def chatSend(self, message, channel):
        self.checkinit()

        post_data = {
            "type": "chatsend",
            "message": message,
            "channel": channel,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            return True
        else:
            return False

    def checkinit(self):
        if not self.initialized:
            print("Initialize first, in order to use the functions")
            time.sleep(3)
            os._exit(1)

    def changeUsername(self, username):
        self.checkinit()

        post_data = {
            "type": "changeUsername",
            "newUsername": username,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }

        response = self.__do_request(post_data)

        json = jsond.loads(response)

        if json["success"]:
            print("Successfully changed username")
        else:
            print(json["message"])
            time.sleep(3)
            os._exit(1)        
            
    def __do_request(self, post_data):
        try:
            response = requests.post(
                "https://keyauth.win/api/1.2/", data=post_data, timeout=10
            )
            
            key = self.secret if post_data["type"] == "init" else self.enckey
                        
            client_computed = hmac.new(key.encode('utf-8'), response.text.encode('utf-8'), hashlib.sha256).hexdigest()
            
            signature = response.headers["signature"]
            
            if not hmac.compare_digest(client_computed, signature):
                print("Signature checksum failed. Request was tampered with or session ended most likely.")
                print("Response: " + response.text)
                time.sleep(3)
                os._exit(1) 
            
            return response.text
        except requests.exceptions.Timeout:
            print("Request timed out. Server is probably down/slow at the moment")

    class application_data_class:
        numUsers = numKeys = app_ver = customer_panel = onlineUsers = ""

    class user_data_class:
        username = ip = hwid = expires = createdate = lastlogin = subscription = subscriptions = ""

    user_data = user_data_class()
    app_data = application_data_class()

    def __load_app_data(self, data):
        self.app_data.numUsers = data["numUsers"]
        self.app_data.numKeys = data["numKeys"]
        self.app_data.app_ver = data["version"]
        self.app_data.customer_panel = data["customerPanelLink"]
        self.app_data.onlineUsers = data["numOnlineUsers"]

    def __load_user_data(self, data):
        self.user_data.username = data["username"]
        self.user_data.ip = data["ip"]
        self.user_data.hwid = data["hwid"] or "N/A"
        self.user_data.expires = data["subscriptions"][0]["expiry"]
        self.user_data.createdate = data["createdate"]
        self.user_data.lastlogin = data["lastlogin"]
        self.user_data.subscription = data["subscriptions"][0]["subscription"]
        self.user_data.subscriptions = data["subscriptions"]