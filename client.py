import httpx

from flask import current_app

pan_base_url: str = 'https://pan.baidu.com'

async def get_json_resource(url, **kwargs):
  resp = {}
  arg_headers = kwargs.get('headers', {})
  headers: dict = {'Content-Type': 'application/json', **arg_headers}
  timeout: httpx.Timeout = httpx.Timeout(60, read=600, connect=60)
  client: httpx.AsyncClient = httpx.AsyncClient(verify=False, timeout=timeout)
  handler = await client.get(url, headers=headers)
  resp = handler.json()
  await client.aclose()
  return resp

def get_token() -> str:
  config = current_app.config or object()
  return config.get('STORAGE_TOKEN', '')

async def upload_file() -> str:
  token = await get_token()
  return f'token: {token}'

async def list_storage() -> list:
  token = get_token()
  url = f'{pan_base_url}/rest/2.0/xpan/file?method=list&access_token={token}&dir=/storage&limit=10&web=web&folder=0'
  return await get_json_resource(url)
