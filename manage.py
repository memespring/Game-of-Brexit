from flask_script import Manager, prompt_bool
from legitag import app, models
import feedparser
from mongoengine import connect, DoesNotExist
from time import sleep
import re
import os
import csv

manager = Manager(app)

@manager.command
def resetdatabase():
    "Delete all data, reset everything"
    if prompt_bool("Are you absolutely certain you want to delete all this things?"):

      db = connect(app.config['MONGODB_DB'], host=app.config['MONGODB_HOST'],  port=app.config['MONGODB_PORT'])
      db.drop_database(app.config['MONGODB_DB'])
      print("Deleted all collections from database ...")

@manager.command
def generateleaguetable():
    ledger = {'0': {'user': None, 'count': 0}}
    legislations = models.Legislation.objects()
    for legislation in legislations:
        for edit in legislation._edits:
            if not edit.user:
                ledger['0']['count'] += 1
            elif edit.user.id in ledger:
                ledger[edit.user.id]['count'] += 1
            else:
                ledger[edit.user.id] = {'user': edit.user, 'count': 1}
    
    models.EditCount.drop_collection()
    for key, value in ledger.items():

        edit_count = models.EditCount()
        edit_count.user = value['user']
        edit_count.count = value['count']
        edit_count.save()

@manager.command
def importdata():
    f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/regulations.csv'))
    reader = csv.reader(f)
    next(reader, None)
    for row in reader:
        legislation = models.Legislation()
        legislation.title = row[5]
        if row[1] != '':
            legislation.original_url = row[1]
        else:
            legislation.original_url = row[0]
        legislation.html_url = row[0]
        try:
            legislation.save()
        except:
            print "Failed to import: %s" % row.join(',')

if __name__ == "__main__":
    manager.run()