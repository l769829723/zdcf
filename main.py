from flask import Flask, render_template, g
from extensions import account_spliter, job_worker
from setting import get_config

def regist_hooks(app):
  @app.before_first_request
  def regist_g():
    pass


def get_app(config: object) -> Flask:
  # 初始化程序
  app = Flask('webapp')

  # 初始化配置
  app.config.from_object(config)

  # 使用扩展
  with app.app_context():
    account_spliter.init_app(app)
    job_worker.init_app(app)
  
  regist_hooks(app)

  # 注册路由模块
  from routes import view
  app.register_blueprint(view)
  
  return app

if __name__ == '__main__':
  config = get_config()
  app = get_app(config)
  app.run(host='0.0.0.0', port=81)