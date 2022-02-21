import json
import requests
from flask import jsonify, request, session, redirect

api_url = "https://aip-confort.milebits.com:3001"

class User:

    @property
    def signup(self):
        print(request.form)
        # user object
        user = {
            "email": request.form.get('email'),
            "password": request.form.get('pass'),
            "username": request.form.get('username')
        }
        confirm = request.form.get('pass2')
        if confirm != user['password']:
            message = "Passwords are not similar"
            return jsonify({"message": message, "status": "failed"}), 401
        else:
            user = json.dumps(user)
            url = f"{api_url}/signup"
            resp = requests.post(url, json=user)
            message = resp.json()['message']
        if resp.json()['status'] == "successful":
            print("success")
            return jsonify({"use": user, "status": "successful"}), 200
        return jsonify({"message": message, "status": "failed"}), 401


class login_user:
    @property
    def login(self):
        user_login = {
            "email": request.form.get('email'),
            "password": request.form.get('pass')
        }
        user = json.dumps(user_login)
        url = f"{api_url}/login"
        resp = requests.post(url, json=user_login)
        message = resp.json()['message']
        token = resp.json()['data']['user']['token']
        user = resp.json()['data']['user']
        # self.start_session(user, token)
        if resp.json()['status'] == "successful":
            return self.start_session(user, token)
        return jsonify({"message": message, "status": "failed"}), 401

    def start_session(self, user_login, token):
        session['logged_in'] = True
        session['user_login'] = user_login
        session['token'] = token
        return jsonify({"user": user_login, "token": token}), 200

    def signout(self):
        session.clear()
        return jsonify({"status": "success", "singedOut": True})
        #return redirect('/')

    def current_token(self):
        token = session['token']
        return token