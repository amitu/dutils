RDebug -- werkzeug based debug server
*************************************

.. include:: global.rst

|dutils| bundles a managemenent command `rdebug`. This command is a replacement
for runserver, to facilitate debugging.

.. note::

    This feature requires :mod:`werkzeug`, install it using::

        easy_install -U werkzeug

This is dangerous if exposed to world
=====================================

First things first, this is a development tool, and very dangerous one.

.. warning::

    Like django's `runserver`, `rdebug` is not meant for production and should
    be used only in very controlled setup, as it allows arbitrary code
    execution from browser.

    `rdebug` is more dangerous than `runserver`.

Why use it
==========

Django gives a very helpful page when something goes wrong, like a server
error, that page contains local variables and few lines of code for the entire
stack.

Sometimes that is not suffecient, may be it hides the values inside objects and
only show string representation of objects, sometimes more lines of code would
be helpful, and sometimes its handy to interact with the internal state of the
objects.

`rdebug` gives a ajax shell at each frame in the context, and python code can
be executed from within the browser. `rdebug` also lets you see entire python
file, not just a few lines.

How to use
==========

Now that warning and motivation is understood, here is how to use it::

    $ python manage.py rdebug

This required you have added |dutils| to your installed apps, place the
following in settings if not already done::

    INSTALLED_APPS = (
        # others
        "dutils",
    )

`rdebug` optionally takes `--ip` and `--port` parameters, and their default
values are `ip=localhost` and `port=8001`.::

    $ python manage.py rdebug --ip 0.0.0.0 --port 80

Never do that! :-)

