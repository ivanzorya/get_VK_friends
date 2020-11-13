import os
import random

import requests
from flask import Flask, render_template, request, make_response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

REDIRECT_URL = os.getenv('REDIRECT_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def get_token(code):
    token = requests.post(f'https://oauth.vk.com/access_token?'
                          f'client_id={CLIENT_ID}&'
                          f'client_secret={CLIENT_SECRET}&'
                          f'redirect_uri={REDIRECT_URL}&code={code}')
    return token.json().get('access_token')


def get_user_data(token, id=None):
    if id is not None:
        user_data = requests.post(
            f'https://api.vk.com/method/users.get?user_id={id}&'
            f'v=5.21&access_token={token}')
    else:
        user_data = requests.post(f'https://api.vk.com/method/users.get?&'
                                  f'v=5.21&access_token={token}')
    first_name = user_data.json().get('response')[0].get('first_name')
    last_name = user_data.json().get('response')[0].get('last_name')
    id = user_data.json().get('response')[0].get('id')
    return {
        'first_name': first_name,
        'last_name': last_name,
        'id': id
    }


def get_user_friends(user_id, token):
    friends_list = requests.post(f'https://api.vk.com/method/friends.get?'
                                 f'user_id={user_id}&'
                                 f'v=5.124&access_token={token}')
    return friends_list.json().get('response').get('items')


def get_friends_names(token, friend_indexes):
    friends = []
    for i in friend_indexes:
        friend = get_user_data(token, i)
        friends.append(friend)
    data = []
    for i in friends:
        name = i.get('first_name') + ' ' + i.get('last_name')
        data.append(name)
    return data[0], data[1], data[2], data[3], data[4],


@app.route('/')
def index():
    code = None
    if 'code' in request.url:
        prom = request.url.split('=')
        code = prom[1]
    if code is None:
        code = request.cookies.get('Code')
    friends_list = None
    friend_indexes = None
    friends = request.cookies.get('Friends')
    token = request.cookies.get('Token')
    username = request.cookies.get('Username')
    if friends is not None:
        friend_indexes = friends.split()
    if code is not None:
        if friend_indexes is not None:
            f0, f1, f2, f3, f4 = get_friends_names(token, friend_indexes)
            response = make_response(render_template(
                'index.html',
                code=code, username=username, f0=f0, f1=f1, f2=f2, f3=f3, f4=f4
            ))
            return response
        token = get_token(code)
        if token is not None:
            user_data = get_user_data(token)
            username = user_data.get('first_name') + ' ' + user_data.get('last_name')
            friends_list = get_user_friends(user_data.get('id'), token)
        if friends_list is not None:
            friend_indexes = random.sample(friends_list, 5)
            friend_indexes = [str(i) for i in friend_indexes]
            f0, f1, f2, f3, f4 = get_friends_names(token, friend_indexes)
            response = make_response(render_template(
                'index.html',
                code=code, username=username, f0=f0, f1=f1, f2=f2, f3=f3, f4=f4
            ))
            if friend_indexes is not None:
                response.set_cookie('Friends', ' '.join(friend_indexes))
                response.set_cookie('Code', code)
                response.set_cookie('Token', token)
                response.set_cookie('Username', username)
            return response
    return render_template(
        'index.html',
        code=code, redirect_url=REDIRECT_URL, client_id=CLIENT_ID
    )


if __name__ == "__main__":
    app.run(debug=True)
