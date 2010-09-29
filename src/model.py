'''
Created on 29/09/2010

@author: danilo
'''
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api.labs import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import InvalidURLError, DownloadError

#in minutes
COUNTDOWN=15

# Data Models
class Application(db.Model):
    name = db.StringProperty(required=True)
    url = db.StringProperty(required=True)
    addedBy = db.UserProperty(required=True)
    
    
class AppStatus(db.Model):
    app = db.ReferenceProperty(Application)
    status = db.StringProperty(required=True, choices=set(["UP", "DOWN", "WARNING"]))
    message = db.StringProperty(default="")
    date = db.DateProperty()

# Business Logic
class modelFacade():
    def addApplication(self, name, url):
        user = users.get_current_user() 
        app = Application(name=name, url=url, addedBy=user)
        app.put()

    def monitorApps(self, cursor=None):
        batch_size = 5

        query = Application.all()
        if cursor: 
            query.with_cursor(cursor)

        apps = Application.all().fetch(5)
        
        for app in apps:
            appStatus = None
            try:
                result = urlfetch.fetch(app.url)
                if result.status_code == 200:
                    appStatus = AppStatus(app = app, status = "UP")
                else:
                    appStatus = AppStatus(app = app, status = "WARNING", message = "Status code " + result.status_code)
            except InvalidURLError:
                appStatus =  AppStatus(app = app, status = "DOWN", message = "Invalid URL!")
            except DownloadError:
                appStatus =  AppStatus(app = app, status = "DOWN", message = "Application not answer!")
                
            appStatus.put()
        
        if len(apps) > batch_size:
            taskqueue.add(url='/monitor', method='POST', params={'cursor': query.cursor()})
    
        taskqueue.add(url='/monitor', method='POST', countdown=COUNTDOWN*60)

    def getAppStatus(self):
        apps = Application.all().order("name")
        status = []
        
        for app in apps:
            query = AppStatus.all()
            query.filter("app =", app.key())
            query.sort("date")
            appStatus = query.fetch(1)
            appStatus.appName = app.name
            status.append(appStatus)
                