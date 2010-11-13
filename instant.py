"""
Interface with mongodb.
"""
import pymongo
from pymongo import Connection
import re
import sys
import json
from flask import Flask,url_for

app = Flask(__name__)
connection = None
db = None
t = None
dbname = 'test'
tagscollection = 'tags'
started = False

def log(s):
    print s

def start():
    global connection, db, dbname
    global tagscollection, t, started
    if started:
        return
    connection = Connection()
    db = connection[dbname]
    t = db[tagscollection]
    started = True

def stop():
    started = False
    pass

def read_ctags(fname):
    lines = open(fname).readlines()
    lst = []
    for l in lines:
        try:
            if l.startswith('!'):
                continue
            l = l.strip()
        # tok, file, vimcmd, opts
            tok, file, rest = l.split('\t',2)
            pat, opt = rest.strip().split('"\t', 1)
            opts = opt.strip().split('\t')
            row = { 'token': tok,
                    'file': file }
            row.update(dict(map(lambda i: tuple(i.split(':',1)), opts)))
            lst.append(row)
        except:
            pass
    return lst

def populate_db(fname):
    start()
    tags = read_ctags(fname)
    t.insert(tags)

def drop_db():
    start()
    db.drop_collection(tagscollection)

def index():
    """Sets up an index for the particular column."""
    start()
    log("Creating indices..")
    t.create_index([
            ("token", pymongo.ASCENDING),
            ("file", pymongo.ASCENDING),
            ])
    log("Done creating indices..")

def prefix_search(limit=20,**kwargs):
    start()
    dic = {}
    for k,v in kwargs.iteritems():
        dic[k] = {'$regex': '^%s' % v}
    results = t.find(dic, limit=limit)
    ret = []
    for item in results:
        ret.append({'token':item['token'], 'file':item['file']})
    return ret

#populate_db('tags')
#index()
#sample()
#prefix_search(limit=10, token='tcp_xmit')

@app.route('/token/<prefix>')
def search(prefix):
    return json.dumps(prefix_search(limit=20, token=prefix))

if __name__ == "__main__":
    app.run()
