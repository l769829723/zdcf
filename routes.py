import os
import json
import traceback

from replit import db
from datetime import datetime
from flask import Blueprint, render_template, redirect, request, flash, current_app, send_file
from werkzeug.utils import secure_filename

__all__ = [
  'view'
]

view = Blueprint('View', 'default_view', url_prefix='/')

@view.get('/')
async def home_page():
  # account_spliter.execute_split()
  return render_template('index.html')


@view.get('/jobs/<job_id>')
async def get_job_details(job_id):
  current_app.logger.info(f'Listing job {job_id} ...')
  jobs = json.loads(db.get('jobs') or '{}')
  job = jobs.get(job_id, {})
  place=job.get('filename', '')
  message = job.get('message', '')
  progress = job.get('progress', 0)
  if not place:
    flash('访问的页面丢失啦～')
    return redirect('/')
  return render_template('detail.html', message=message, progress=progress, job=job_id)


@view.get('/download/<job_id>')
async def download_job_attachment(job_id):
  current_app.logger.info(f'Listing job {job_id} ...')
  jobs = json.loads(db.get('jobs') or '{}')
  job = jobs.get(job_id, {})
  place=job.get('zipfile', '')
  if not place:
    flash('访问的页面丢失啦～')
    return redirect('/')
  return send_file(place, as_attachment=True)


@view.post('/')
async def split_assets():
  try:
    jobs = json.loads(db.get('jobs') or '{}')
    ts = int(datetime.now().timestamp() * 1000)
    file = request.files['assets']
    full_filename = secure_filename(file.filename)
    storage_path = current_app.config['UPLOAD_FOLDER']
    filename, ext_name = os.path.splitext(full_filename)
    _renamed = f'_{filename}_{ts}{ext_name}'
    saved_path = os.path.join(storage_path, _renamed)
    file.save(saved_path)
    current_app.logger.info(f'The file will be saved in {saved_path}')
    jobs[ts] = { 'filename': _renamed }
    db['jobs'] = json.dumps(jobs)
    flash('上传完成了!')
    return redirect(f'/jobs/{ts}')
  except Exception as exp:
    current_app.logger.error(traceback.format_exc())
    flash('服务器故障, 请重试!')
  return redirect('/')
