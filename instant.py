"""
Interface with mongodb.
"""
import pymongo
from pymongo import Connection
import re
import sys
import json
from flask import Flask,url_for,redirect

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
                    'filename': file }
            row.update(dict(map(lambda i: tuple(i.split(':',1)), opts)))
            lst.append(row)
        except:
            pass
    return lst

def populate_db(fname):
    start()
    log('Reading tags')
    tags = read_ctags(fname)
    t.insert(tags)
    log('Populated db')

def drop_db():
    start()
    db.drop_collection(tagscollection)

def index():
    """Sets up an index for the particular column."""
    start()
    log("Creating indices..")
    t.create_index([
            ("token", pymongo.ASCENDING),
            ("filename", pymongo.ASCENDING),
            ])
    log("Done creating indices..")

def db_search(limit=20,**kwargs):
    start()
    dic = {}
    for k,v in kwargs.iteritems():
        dic[k] = {'$regex': '%s' % v}
    results = t.find(dic, limit=limit)
    ret = []
    count = results.count()
    for item in results:
        ret.append({
                'token':item['token'],
                'filename':item['filename'],
                'line':item['line'],
                'kind':item['kind'],
                })
    return {'count': count, 'results': ret}

#populate_db('tags')
#index()
#sample()

def preprocess(s):
    ret = {}
    allowed_keys = ["token","file","kind","lang"]

    if ":" in s:
        items = re.split('\s+', s)
        for i in items:
            if ":" in i:
                k,v = map(lambda x: x.strip(), i.split(":"))
                if k in ['function', 'macro', 'member','struct']:
                    ret['kind'] = k
                    ret['token'] = '^%s' % v
                elif k in ['file']:
                    ret['filename'] = v
                else:
                    ret[k] = v
            elif not ret.has_key('token'):
                ret['token'] = i
    else:
        ret['token'] = '^%s' % s
    return ret

#print preprocess('file:lo')
#sys.exit(0)

@app.route('/token/<s>')
def search(s):
    if len(s) <= 1:
        return json.dumps([])
    args = preprocess(s)
    # simple prefix search
    ret = db_search(limit=20, **args)
    # full text search
    if len(ret) < 10:
        try:
            args['token'] = args['token'][1:] # remove the ^
        except:
            args['token'] = ''
            del args['token']
        ret = db_search(limit=20, **args)
    return json.dumps(ret)

@app.route('/')
def main():
    return redirect('/static/index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

