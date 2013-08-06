#!/usr/bin/python

import getpass
import json
import string
import urllib2

def login(email, password):
    request = urllib2.Request('https://auth-staging.prod.sagebase.org/auth/v1/session')
    request.add_header('Accept', 'application/json')
    request.add_header('Content-Type', 'application/json')
    data = json.dumps({'email' : email, 'password' : password})
    try:
        response = urllib2.urlopen(request, data)
        response_body = response.read()
        response.close()
        results = json.loads(response_body)
        session = results['sessionToken']
        return session
    except urllib2.HTTPError, e:
        print e.code, e.msg

def load_evals(eval_file):
    print 'Reading file ', eval_file
    with open(eval_file) as f:
        lines = f.readlines()
        f.close
        print 'Number of eval IDs loaded: ', len(lines)
        return lines

def backfill_acl(session_token, eval_list):
    for eval_id in eval_list:
        eval_id = eval_id.strip()
        print 'Backfilling ', eval_id
        url = 'https://repo-staging.prod.sagebase.org/repo/v1/evaluation/'
        url = url + eval_id
        url = url + '/acl'
        request = urllib2.Request(url)
        request.add_header('Accept', 'application/json')
        request.add_header('Content-Type', 'application/json')
        request.add_header('sessionToken', session_token)
        try:
            response = urllib2.urlopen(request)
            response_body = response.read()
            response.close()
            acl = json.loads(response_body)
            print 'Backfilled ', acl['id']
        except urllib2.HTTPError as e:
            print e.code, e.msg


email = raw_input('Email: ')
password = getpass.getpass('Password: ')
session_token = login(email, password)
print session_token
eval_file = raw_input('Eval File: ')
eval_list = load_evals(eval_file)
backfill_acl(session_token, eval_list)

