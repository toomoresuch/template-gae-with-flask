# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#  IMPORTS.
# ------------------------------------------------------------------------------

from flask import Flask
from flask import abort
from flask import flash
from flask import get_flashed_messages
from flask import redirect
from flask import request
from flask import url_for
from google.appengine.api import users
from google.appengine.ext import db
from utils.decorators import templated

# ------------------------------------------------------------------------------
#  CONFIGURATION.
# ------------------------------------------------------------------------------

app = Flask(__name__)

# set the secret key.  keep this really secret:

app.secret_key = 'the secret key'
app.debug = True

# ------------------------------------------------------------------------------
#  MODELS.
# ------------------------------------------------------------------------------


class Task(db.Model):

    user = db.UserProperty()
    name = db.StringProperty(required=True)
    done = db.BooleanProperty()


# ------------------------------------------------------------------------------
#  METHODS.
# ------------------------------------------------------------------------------


@app.route('/')
@templated()
def list():
    user = users.get_current_user()
    tasks = Task.all().filter('user =', user)
    return dict(user=user, logout_url=users.create_logout_url('/'),
                tasks=tasks, flashes=get_flashed_messages())


@app.route('/', methods=['POST'])
def task_post():
    name = request.form['name']
    if not name:
        flash('Oops you forgot to set a task name.')
        return redirect(url_for('list'))
    task = Task(name=request.form['name'])
    task.user = users.get_current_user()
    task.put()
    return redirect(url_for('list'))


@app.route('/delete/<int:id>')
def task_delete(id):
    task = Task.get_by_id(id)
    if task and task.user == users.get_current_user():
        task.delete()
    else:
        abort(404)

    return redirect(url_for('list'))


@app.route('/done/<int:id>')
def task_done(id):
    task = Task.get_by_id(id)
    if task and task.user == users.get_current_user():
        if task.done:
            task.done = False
        else:
            task.done = True
        task.put()
    else:
        abort(404)

    return redirect(url_for('list'))

# ------------------------------------------------------------------------------
#  MAIN.
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run()

