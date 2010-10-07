'''
Created on 29/09/2010

@author: Danilo Penna Queiroz
'''
import logging
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
	application = db.StringProperty(required=True)
	status = db.StringProperty(choices=set(["UP", "DOWN", "WARNING"]), default = "DOWN")
	message = db.StringProperty(default="")
	date = db.DateProperty()

# Business Logic
class ModelFacade():
	def addApplication(self, name, url):
		logging.info("Adding application %s : %s"%(name,url))
		user = users.get_current_user() 
		if user:
			app = Application(name=name, url=url, addedBy=user)
			app.put()
	def monitorApps(self, cursor=None):
		batch_size = 5
		query = Application.all()
		if cursor: 
			query.with_cursor(cursor)
		apps = query.fetch(batch_size)
		logging.debug("Will now check status for %d applications."%len(apps))
		#check apps status		
		for app in apps:
			logging.info("Checking %s's status"%app.name)
			appStatus = AppStatus(application = app.name)
			try:
				result = urlfetch.fetch(app.url)
				if result.status_code == 200:
					appStatus.status = "UP"
				else:
					appStatus.status = "WARNING"
					appStatus.message = "Status code " + result.status_code
			except InvalidURLError:
				logging.error("Unable to check %s's status: Invalid URL!"%app.name)
				appStatus.status = "DOWN"
				appStatus.message = "Invalid URL!"
			except DownloadError:
				logging.error("Unable to check %s's status: Application not answer!"%app.name)
				appStatus.status = "DOWN"
				appStatus.message = "Application not answer!"
			#save status
			appStatus.put()
		#check other apps if necessary
		if len(apps) > batch_size:
			taskqueue.add(url='/monitor', method='POST', params={'cursor': query.cursor()})
		#enqueue periodic check
		taskqueue.add(url='/monitor', method='POST', countdown=COUNTDOWN*60)
		
	def getAppStatus(self):
		logging.info("Loading applications status")
		apps = Application.all().order("name")
		status = []	
		for app in apps:
			query = AppStatus.all()
			query.filter("application =", app.name)
			query.order("date")
			results = query.fetch(1)
			if len(results) ==1:
				appStatus = results.pop()
				status.append(appStatus)
		return status
	
