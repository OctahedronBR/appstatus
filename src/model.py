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

# Data Models
class Application(db.Model):
	name = db.StringProperty(required=True)
	url = db.StringProperty(required=True)
	addedBy = db.UserProperty(required=True)
	
	
class AppStatus(db.Model):
	application = db.ReferenceProperty(Application, collection_name="status")
	status = db.StringProperty(choices=set(["UP", "DOWN", "WARNING"]), default = "DOWN")
	message = db.StringProperty(default="")
	date = db.DateTimeProperty(auto_now_add=True)

# Business Logic
class ModelFacade():
	def addApplication(self, name, url):
		"""
		Adds a new application to be monitored
		"""
		logging.info("Adding application %s : %s"%(name,url))
		user = users.get_current_user() 
		if user:
			app = Application(name=name, url=url, addedBy=user)
			app.put()
			
	def selectApps(self, cursor):
		"""
		Selects the applications to be checked. For each request it selects up to 5 applications to
		perform the check. The given cursor is used to determine which applications to choice.
		If necessary, it enqueues a task to check the remained applications.
		It returns a list that contains the applications to be checked.
		"""
		batch_size = 5
		query = Application.all()
		if cursor: 
			query.with_cursor(cursor)
		apps = query.fetch(batch_size)
		#check other apps if necessary
		if len(apps) == batch_size:
			taskqueue.add(url='/task/monitor', method='POST', params={'cursor': query.cursor()})
		return apps
		
	def monitorApps(self, cursor=None):
		"""
		Checks the applications status. 
		The check is made fetching the application page, by url, and checking
		the response code. If the response code is 200, application is considered to be
		UP and running, if it's 404 or it doesn't answer, application is DOWN, any other response it's considered
		a WARNING.
		"""
		apps = self.selectApps(cursor)
		logging.debug("Will now check status for %d applications."%len(apps))
		#check apps status		
		for app in apps:
			logging.info("Checking %s's status"%app.name)
			appStatus = AppStatus(application = app)
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
		
		
	def getAppStatus(self):
		logging.info("Loading applications status")
		apps = Application.all().order("name")
		logging.debug("There's %d applications registred" % apps.count())
		status = []
		for app in apps:
			logging.info("Check status for app %s" % app.name)
			result = app.status.order("-date").get()
			if result:
				logging.debug("Status found for application %s" % app.name)
				status.append(result)
		return status
	
