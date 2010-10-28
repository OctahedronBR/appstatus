'''
Created on 29/09/2010

@author: Danilo Penna Queiroz
'''
import os
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import users
from model import ModelFacade

model = ModelFacade()

class RegisterApp(webapp.RequestHandler):
	@login_required
	def get(self):
    	# render register
		path = os.path.join(os.path.dirname(__file__), 'register.html')
		self.response.out.write(template.render(path, {}))
 	
	def post(self):
		appName = self.request.get('name')
		url = self.request.get('url')
		model.addApplication(appName, url)
		self.redirect("/register")
        
class ShowStatus(webapp.RequestHandler):
	def get(self):
		status = model.getAppStatus()
		template_values = { 'status':status }
		# check failed applications
		failed = []
		for app in status:
			if app.status != 'UP':
				failed.append(app.app.name)
		if len(failed) > 0:
			template_values['failed'] = failed
		# render template
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))

class Monitor(webapp.RequestHandler):
	def get(self):
		model.monitorApps(self.request.get('cursor'))
			
# Application entry point
application = webapp.WSGIApplication(
                                     [('/', ShowStatus), 
                                      ('/task/monitor', Monitor), 
                                      ('/register', RegisterApp)], 
                                      debug=True)


def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
