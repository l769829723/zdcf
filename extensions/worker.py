import time
import traceback
import threading

import utils

from replit import db
from flask import current_app
from flask.cli import with_appcontext

class JobWorker:
  def __init__(self, app=None):
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
    def run_jobs():
      while True:
        time.sleep(60)
        app.logger.info('Waiting for incoming jobs ...')
        jobs = utils.get_job_list()
        
        for job, payload in jobs.items():
          try:
            spliter = getattr(app, 'spliter', None)
            progress = payload.get('progress', 0)
            if progress < 100:
              if not spliter:
                raise Exception('Spliter not found!')
              result_path = spliter(job)
              payload['zipfile'] = result_path
              payload['progress'] = 100
              payload['message'] = ''
              utils.save_job(job, payload)
          except:
            payload['message'] = '服务器故障！'
            app.logger.info(traceback.format_exc())
            payload['progress'] = 100
            utils.save_job(job, payload)
            time.sleep(180)

    tasks = threading.Thread(name='app_worker', target=run_jobs)
    tasks.start()
