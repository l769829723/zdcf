import json

from replit import db

def get_job_list():
    try:
      return json.loads(db.get('jobs'))
    except:
      return {}

def get_job_by_id(job):
  jobs = get_job_list()
  return jobs.get(job, None)


def save_job(job, data):
  jobs = get_job_list()
  jobs[job] = data
  db['jobs'] = json.dumps(jobs)
