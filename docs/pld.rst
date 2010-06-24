Project Less Django -- dutils.pld
*********************************

.. include:: global.rst

Getting started with django is rather tedious. One has to learn and create a
project, and an application at the minimum. One also has to understand
settings, add the newly created app to INSTALLED_APPS and so forth. 

|pld| aims to avoid all this.

Starting Server
===============

To start using |pld| invoke it using the command line::

    $ python -m dutils.pld runserver
    Validating models...
    0 errors found

    Django version 1.2.1, using settings None
    Development server is running at http://127.0.0.1:8000/
    Quit the server with CONTROL-C.

This will start a development server.

Note that you can do it from any directory. Once it is running we can start
writing python modules that will be served by django.

Handler Modules
===============

A minimalistic hello world module would be, hello.py::

    def handle(request):
        return "hello world"

Save this file, and visit http://127.0.0.0:8000/hello/. Thanks to django's
runserver's auto reload feature, any changed made in hello.py will be reflected
without requiring a restart by developer.

Each handler module must define a method named `handle`. This method will take
one parameter, `request`. Request is an instance of HttpRequest_ class.

`handle` must return either a string or a subclass of HttpResponse_ object.

An example of a `handle` that redirects user to a different page::

    from django.http import HttpResponseRedirect

    def handle(request):
        return HttpResponseRedirect("/")


Templates Are Configures
========================

|pld| configures django to serve templates from a folder named `templates` in
the current directory.

This means handlers can use django's template system for serving, for example::

    from django.shortcuts import render_to_response
    from datetime import datetime

    def handle(request):
        current_time = datetime.now()
        return render_to_response(
            "index.html", {"current_time": current_time}
        )

To use the template, create a folder named `templates` in current folder, and
store `index.html` in it:

.. code-block:: django

    <h1>Current time is {{ current_time }}</h1>

Serving Static Media
====================

To help developers to quickly start getting their hands dirty with django,
|pld| configures django to serve files stored in a folder named `static`.

To use this feature, create a folder named `static` in your current directory,
store a file `style.css` in it. That file will be available at
http://127.0.0.1:8000/static/style.css.

Files can be organized into folders inside `static` folder, so a file named
`static/js/jquery.js` will be server on
http://127.0.0.1:8000/static/js/jquery.js for example.

Settings
========

While |pld| takes care of setting up all settings required by django, it may be
so that more settings are still required. To set any settings, create a file
`settings.py` in the current folder, and it will overwrite settings used by
|pld|.

Example settings.py::

    TEMPLATE_DIRS = ["templates2"]
    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.contrib.messages.context_processors.messages"
    )
