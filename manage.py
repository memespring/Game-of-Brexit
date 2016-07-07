from flask_script import Manager, prompt_bool
from legitag import app, models
import feedparser
from mongoengine import connect
from time import sleep
import re

manager = Manager(app)

@manager.command
def resetdatabase():
    "Delete all data, reset everything"
    if prompt_bool("Are you absolutely certain you want to delete all this things?"):

      db = connect(app.config['MONGODB_DB'], host=app.config['MONGODB_HOST'],  port=app.config['MONGODB_PORT'])
      db.drop_database(app.config['MONGODB_DB'])
      print("Deleted all collections from database ...")

@manager.command
def importdata():

    keep_going = True
    page = 1
    while keep_going:
        
        print "Importing page %s ..." % page

        result = feedparser.parse('http://www.legislation.gov.uk/uksi/data.feed?text=%22European%20Communities%20Act%201972%22&page=' + str(page))

        if int(result.feed['leg_page']) != page:
            # when we reach the end, we get redirected back to page 1
            keep_going = False
        else:
            for item in result.entries:
                legislation = models.Legislation()
                legislation.title = item['title'][0:255]

                #handle case where there are english and welsh titles
                if '<span xml:lang="en">' in legislation.title:
                    match = re.match('<span xml:lang="en">(.*?)</span>', legislation.title)
                    legislation.title = match.group(1)

                for link in item.links:
                    if link['rel'] == 'alternate':
                        if link['type'] == 'application/xhtml+xml':
                            legislation.html_url = link['href']
                        if link['type'] == 'application/pdf':
                            legislation.pdf_url = link['href']
                legislation.save()
                print "Saved %s " % legislation.title

            page = page + 1
            sleep(0.5)


if __name__ == "__main__":
    manager.run()