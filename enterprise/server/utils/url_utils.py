
from fastapi import Request
from openhands.app_server.config import get_global_config


def get_web_url(request: Request):
    web_url = get_global_config().web_url
    if not web_url:
        scheme = 'http' if request.url.hostname == 'localhost' else 'https'
        web_url = f'{scheme}://{request.url.netloc}'
    return web_url

