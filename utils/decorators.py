# -*- coding: utf-8 -*-

from flask import current_app
from flask import render_template
from flask import request
from functools import wraps
from google.appengine.runtime import DeadlineExceededError
from jinja2.exceptions import TemplateNotFound

# ------------------------------------------------------------------------------
#  Decorators.
# ------------------------------------------------------------------------------


def templated(template=None):
    """
    引数 template を省略した場合は、デコレートされた関数の名称をテンプレート名称とする。
    ブラウザからの Accept-Languages の値と同名のディレクトリに収納されたテンプレートを使用する。
    Accept-Languages の値と同名のディレクトリが存在しない場合は、言語コードを強制的に en とする。
    30秒ルールに抵触した場合は、Status 500 のメッセージを出力する。
    """

    def decorator(original_function):

        @wraps(original_function)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint.replace('.', '/')

            template_path = '%s/%s.html' % (request.accept_languages.best,
                    template_name)

            ctx = original_function(*args, **kwargs)
            if ctx is None:
                ctx = {}

            try:
                try:
                    rv = render_template(template_path, **ctx)
                    cl = request.accept_languages.best
                except TemplateNotFound:
                    rv = render_template('en/%s.html' % template_name, **ctx)
                    cl = 'en'
                finally:
                    return current_app.response_class(rv,
                            headers={'Content-Language': cl})
            except DeadlineExceededError:
                return current_app.response_class('Sorry, This operation could not be completed in time...'
                        , status=500, mimetype='text/plain')

        return decorated_function

    return decorator



