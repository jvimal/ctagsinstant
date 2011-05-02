"""
Interface with mongodb.
"""
import pymongo
from pymongo import Connection
import re
import sys
import json
from flask import Flask,url_for,redirect

import argparse
from subprocess import Popen, PIPE
import os
from time import sleep
import termcolor as T

app = Flask(__name__)
connection = None
db = None
t = None
dbname = 'test'
tagscollection = 'tags'
started = False
mongod_process = None

parser = argparse.ArgumentParser(description="ctags instant")
parser.add_argument('--source-dir',
                    '-d',
                    action='store',
                    dest='source_dir',
                    help="Path to the source code's root directory.",
                    required=True)

parser.add_argument('--mongod',
                    '-e',
                    action='store',
                    dest='mongod_path',
                    help="Path to the mongod executable.",
                    default='/usr/local/bin/mongod')

parser.add_argument('--quiet',
                    '-q',
                    action='store_true',
                    dest='quiet',
                    help="Suppress mongod's output.",
                    default=False)

args = None

def log(s):
    print T.colored(s, "yellow")

def check_mongod():
    args.mongod_path = os.path.expanduser(args.mongod_path)
    if os.path.exists(args.mongod_path):
        return True
    retry_path = check_output(["which", "mongod"]).strip()
    if len(retry_path):
        log("Found mongod elsewhere: %s" % retry_path)
        args.mongod_path = retry_path
        return True
    return False

def check_db(db_dir):
    db_dir = os.path.expanduser(db_dir)
    return os.path.exists(db_dir)

def create_db(db_dir):
    try:
        db_dir = os.path.expanduser(db_dir)
        os.mkdir(db_dir)
    except Exception, e:
        log("Couldn't make directory %s.  Check permissions" % db_dir)
        print e
        sys.exit(-1)

def start_mongod(dbpath='db/'):
    if not check_mongod():
        log("Error: mongod not found.")
        sys.exit(-1)
    if not check_db(dbpath):
        log("Database directory %s not found.  creating..." % dbpath)
        create_db(dbpath)
    cmd = "%s --dbpath=\"%s\"" % (args.mongod_path, dbpath)
    if args.quiet:
        ret = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    else:
        ret = Popen(cmd, shell=True)
    return ret

def start():
    global connection, db, dbname
    global tagscollection, t, started
    global mongod_process

    if started:
        return
    args.source_dir = os.path.expanduser(args.source_dir)
    # Start mongodb
    dbpath = os.path.join(args.source_dir, "mongo_db")
    mongod_process = start_mongod(dbpath=dbpath)
    while 1:
        try:
            log("trying to connect to mongod...")
            connection = Connection()
            break
        except:
            sleep(1)
            continue
    dbname = args.source_dir.replace('/','|')
    db = connection[dbname]
    t = db[tagscollection]
    log("Found databases: %s" % (', '.join(connection.database_names())))
    if dbname not in connection.database_names():
        log("Database for this project does not exist.  Creating one...")
        create_project(args.source_dir)
    started = True

def stop():
    started = False
    mongod_process.terminate()
    log("Waiting for mongod to terminate...")
    mongod_process.wait()

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
    log('Reading tags')
    tags = read_ctags(fname)
    t.insert(tags)
    log('Populated db')

def create_project(source_dir):
    # First, we create the TAGS file for this project
    tags_file = os.path.join(source_dir, "tags_mongo")
    log("Creating tags... %s, %s" % ( tags_file, source_dir))
    Popen("ctags -R --fields=+afmikKlnsStz -f \"%s\" \"%s\"" % (tags_file, source_dir),
          shell=True).wait()
    log("Reading tags...")
    populate_db(tags_file)
    index()

def drop_db():
    db.drop_collection(tagscollection)

def index():
    """Sets up an index for the particular column."""
    log("Creating indices..")
    t.create_index([
            ("token", pymongo.ASCENDING),
            ("filename", pymongo.ASCENDING),
            ])
    log("Done creating indices..")

def db_search(limit=20,**kwargs):
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
    try:
        args = parser.parse_args()
        start()
        app.run(host='0.0.0.0', debug=True)
    except Exception, e:
        log("Error...")
        log(`e`)
        stop()
