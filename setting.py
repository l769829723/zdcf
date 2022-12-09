import os


# 通用的配置项
BASE_DIR: str = os.path.dirname(__file__)


class AppConfig:
  DEBUG: str = True
  ENV: str = "development"
  STORAGE_TOKEN:str = os.environ.get('storage_token')
  UPLOAD_FOLDER: str = os.path.join(BASE_DIR, 'uploads')
  # 16MB
  MAX_CONTENT_LENGTH: int = 16 * 1000 * 1000
  SECRET_KEY: str = os.environ.get('APP_SECERT', 'key_placeholder')
  

def get_config():
  return AppConfig()
