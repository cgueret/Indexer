import threading
from wsgiref import simple_server
from selenium import webdriver
import os
import sys

pwd = os.path.abspath(os.path.dirname(__file__))
project = os.path.basename(pwd)
new_path = pwd.strip(project)
activate_this = os.path.join(new_path,'src')
sys.path.append(activate_this)

from app import application

def before_all(context):
    context.thread = threading.Thread(target=application.test_client())
    context.thread.start()
    context.browser = webdriver.Chrome()

def after_all(context):
    context.server.shutdown()
    context.thread.join()
    context.browser.quit()

def before_feature(context, feature):
    model.init(environment='test')
    