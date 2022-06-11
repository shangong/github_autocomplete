import os
import sys
import json
from multiprocessing.pool import ThreadPool
from time import time as timer
from flask import Flask, render_template, jsonify, request
import requests

app = Flask('github-search', template_folder='templates') # template_folder=os.getcwd()

class Payload(object):
    def __init__(self, dict_object):
        self.__dict__ = dict_object

    def __getitem__(self, item):
        return getattr(self, item)


def fetch_commit(item):
    """
    fetch latest commit message and sha for this repository
    :param item:
    :return:
    """
    owner = item.get('owner', dict())
    _item = {
        'repository_name': item.get('name'),
        'created_at': item.get('created_at'),
        'owner_url': owner.get('url'),
        'owner_login': owner.get('login'),
        'avatar_url': owner.get('avatar_url')
    }
    # retrieve latest commit message
    commit_url = item.get('commits_url').replace('{/sha}', '')
    commit_headers = {'username': os.getenv('GMAIL_USERNAME'), 'password': os.getenv('GMAIL_PASSWORD')}
    json_resp = requests.get(commit_url, headers=commit_headers)
    if json_resp.status_code == 200:
        commit_resp = json.loads(json_resp.content)

        # fetch commit message with an sha and set attributes on _item
        commit_body = next(val for val in commit_resp if val.get('sha'))
        if commit_body:
            _item['sha'] = commit_body.get('sha')
            commit = commit_body.get('commit')
            author = commit.get('author')
            _item['commit_author_name'] = author.get('name')
            _item['commit_message'] = commit.get('message')

    return Payload(_item)


@app.route('/api/repo')
def index():
    """
        Github repository search
        :return:
    """
    search_term = request.args.get('search_term', '')
    print(search_term, file = sys.stdout) # log the term
    items = list()

    # query github repository using search term
    repository_url = 'https://api.github.com/search/repositories?q={}'.format(search_term)
    headers = {
        'Accept': 'application/vnd.github.v3+json'
        }
    resp = requests.get(repository_url, headers = headers)
    
    # if Request is successful
    if resp.status_code == 200:
        json_resp = json.loads(resp.content)
        json_items = json_resp.get('items', [])
        print(type(json_items), file=sys.stdout)
        print(json_items, file=sys.stdout)
    
    else:
        return jsonify({
            "code": resp.status_code,
            "message": "request error"
        })

    return jsonify(json_items)


@app.route('/search')
def search():
    return render_template('index.html')


@app.route('/wiki')
def wiki():
    return render_template('wiki.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9876, debug=False, use_reloader=False)
