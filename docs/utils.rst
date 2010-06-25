Utility Functions
*****************

.. include:: global.rst

|dutils| is composed of a lot of miscellaneous utility functions. These
functions are documented here.

Logging
=======

|utils| contains following helpers for loggins.

dutils.utils.logger
-------------------

`dutils.utils.logger` is an instance configured logger. The logging is
configured to store the logs in a file named after the projects, in a folder
called `logs` in the current folder.

For example::

    from dutils import utils

    utils.logger.info("this goes to logs")

Assuming the name of the project is `django_project`, this will send the log
message to a file named `logs/django_project.log`.

dutils.utils.create_logger
--------------------------

.. function:: dutils.utils.create_logger(name=None, level=logging.DEBUG)

    Create a logger by the given name.

    :param name: name of the logger. If its not given, name is derived based on
        the name of the project.
    :type name: string or None.
    :param level: logging level.
    :rtype: logger object.

Usage::

    from dutils import utils
    mail_logger = utils.create_logger("mail_logger")

    def send_mail(*args):
        mail_logger.debug("send_mail called")
        ...
        mail_logger.debug("send_mail done")

The logs will be written in `projdir/logs/mail_logger.log`.

dutils.utils.PrintLogger
------------------------

|utils| contains a PrintLogger class. This can be used to make all print
statements go to main logger as well as on console.

To use it go to some module that is loaded by django during startup,
`urls.py` for example, and write the following::

    import sys
    from dutils.utils import PrintLogger
    sys.stdout = PrintLogger(sys.stdout)

    print "hello log file"

After this "hello log file" will be printed on console as well as it will go in
log file.

.. note::

    You may not want to put this line in settings.py as settings.py is
    loaded by utils.py, which will cause cyclic dependency.

SimpleExceptionHandler
======================

|utils| contains a django middleware that logs exceptions to `logger`. 

This middleware can be used by updating the `settings.py`::

    MIDDLEWARE_CLASSES = (
        # other middlewares
        'dutils.utils.SimpleExceptionHandler',
    )

uuid -- universally unique identifier
=====================================

|utils| contains a `uuid`.

.. function:: dutils.utils.uuid( \*args ):

    Generate a random uuid.

    :param \*args: variable number of arguments.
    :rtype: 32 byte long string, composed of hexadecimal chars.

Usage::

    >>> from dutils import utils
    >>> utils.uuid()
    'e5bd5a3bd2d81edaec9857cc97ec655a'

formatExceptionInfo
===================

update_jpg
==========

get_content_from_path
=====================

send_html_mail
==============

JSONResponse
============

JSONEncoder
===========

batch_gen
=========

cacheable
=========

ajax_validator
==============

SizeAndTimeMiddleware
=====================

mail_exception to admins
========================

templated decorator
===================

assert_or_404
=============

debug_call
==========

QuerySetManager
===============

get_fb_access_token_from_request
================================

LoginForm
=========

JSResponse
==========

log_user_in
===========

Frequently one has to log a user in. Django requires you to know the password
of the user, in order to user `authenticate
<http://docs.djangoproject.com/en/dev/topics/auth/#django.contrib.auth.authenticate>`_
function. This can get inconvenient when you do not have, or know the password.

|utils| comes with a utility method `log_user_in` to help in such a situation.

.. function:: log_user_in(user, request)

    Log the given user in the request's session.

    :param user: user object, instance of User_
    :param request: request object, instance of HttpRequest_
    :rtype: None

This function is typically useful for features like logging a user in after
they have clicked on email confirmation link, or for imporsonate a user etc.

ip_shell - IPython Shell
========================

|utils| comes with a utility function ip_shell, that stops the execution and
launches IPython Shell. This can be used for debugging the context at given
location. ::

    from dutils import utils

    def index(request):
        utils.ip_shell()
        # rest

.. note::

    This should only be used with a debugging server that runs in foreground.

object_list
===========
