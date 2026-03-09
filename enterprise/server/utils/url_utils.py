from typing import Literal

from fastapi import Request
from server.constants import IS_FEATURE_ENV, IS_LOCAL_ENV, IS_STAGING_ENV

from openhands.app_server.config import get_global_config


def get_web_url(request: Request):
    web_url = get_global_config().web_url
    if not web_url:
        scheme = 'http' if request.url.hostname == 'localhost' else 'https'
        web_url = f'{scheme}://{request.url.netloc}/'
    elif not web_url.endswith('/'):
        web_url = f'{web_url}/'
    return web_url


def get_cookie_domain() -> str | None:
    config = get_global_config()
    web_url = config.web_url
    # for now just use the full hostname except for staging stacks.
    return (
        web_url
        if web_url and not IS_FEATURE_ENV and not IS_STAGING_ENV and not IS_LOCAL_ENV
        else None
    )


def get_cookie_samesite() -> Literal['lax', 'strict']:
    # for localhost and feature/staging stacks we set it to 'lax' as the cookie domain won't allow 'strict'
    web_url = get_global_config().web_url
    return (
        'strict'
        if web_url and not IS_FEATURE_ENV and not IS_STAGING_ENV and not IS_LOCAL_ENV
        else 'lax'
    )
