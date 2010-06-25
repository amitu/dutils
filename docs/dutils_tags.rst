Dutils Template Tags
********************

.. include:: global.rst

|dutils| comes with some template tags and filters that can be useful for
django projects.

To use them, make sure |dutils| is added to your settings.py::

    INSTALLED_APPS = (
        # other apps
        "dutils",
    )

To use it one of your templates, place the following towards the top of the
template files:

.. code-block:: django

    {% load dutils_tags %}

clevercss -- tag
================

|dutils| contains a filter for converting CleverCSS_ to css.

.. note::

    CleverCSS is a small markup language for CSS inspired by Python that can be
    used to build a style sheet in a clean and structured way. In many ways
    it's cleaner and more powerful than CSS2 is.

    To install it, do the following::

        $ sudo easy_install CleverCSS

Example usage:

.. code-block:: html+django

    <style>
        {% clevercss %}
        ul#comments, ol#comments:
          margin: 0
          padding: 0

          li:
            padding: 0.4em
            margin: 0.8em 0 0.8em

            h3:
              font-size: 1.2em
            p:
              padding: 0.3em
            p.meta:
              text-align: right
              color: #ddd
        {% endclevercss %}
    </style>

This gets converted to:

.. code-block:: html

    <style>
        ul#comments,
        ol#comments {
          margin: 0;
          padding: 0;
        }

        ul#comments li,
        ol#comments li {
          padding: 0.4em;
          margin: 0.8em 0 0.8em;
        }

        ul#comments li h3,
        ol#comments li h3 {
          font-size: 1.2em;
        }

        ul#comments li p,
        ol#comments li p {
          padding: 0.3em;
        }

        ul#comments li p.meta,
        ol#comments li p.meta {
          text-align: right;
          color: #dddddd;
        }
    </style>


gravatar -- filter
==================

This filter can be applied on email addresses, and coverts it to URL that can
be used as part of <img> tag:

.. code-block:: html+django

    <img src="{{ user.email|gravatar }}">

This tag uses service provided by gravatar_.

Configurations
--------------

`gravatar` filter takes three optional parameters. There are three things to
configure for gravatar_:

1. size: this can vary from 1px to 512px, tho its larger sizes may lead to low
   resulutions. The default used by gravatar tag is 80px.

2. ratings: gravatar_ lets users self rate their images, these are the
   available options:

   * g: suitable for display on all websites with any audience type.
   * pg: may contain rude gestures, provocatively dressed individuals, the
     lesser swear words, or mild violence.
   * r: may contain such things as harsh profanity, intense violence, nudity,
     or hard drug use.
   * x: may contain hardcore sexual imagery or extremely disturbing violence

   The default used by `gravatar` filter is `g`.

3. default image: when the given email address is not associated with any
   image, then gravatar serves a default image. `gravatar` has a few predefined
   options:

     * 404: do not load any image if none is associated with the email hash,
       instead return an HTTP 404 (File Not Found) response

     * mm: (mystery-man) a simple, cartoon-style silhouetted outline of a
       person (does not vary by email hash)

     * identicon: a geometric pattern based on an email hash

     * monsterid: a generated 'monster' with different colors, faces, etc
       wavatar: generated faces with differing features and backgrounds

   `gravatar` filter also allows you to specify the default image in
   `settings.py`, this setting is named `GRAVATAR_DEFAULT_URL`.

   The default used by `gravatar` is `identicon`, which looks like this:

   .. figure:: http://www.gravatar.com/avatar/e5b48aec07710c08d5r&d=identicon
      :align: center

      default=identicon

All these parameters can be specified as argument to `gravatar` tag:

.. code-block:: html+django

    <img src="{{ user.email|gravatar:"48:pg:mm" }}>

The order of paramters is size:rating:default. If only one parameter is
specified, its assumed to be size, if two are provided, its size and rating,
and if all three are passed, its size, rating and default.

.. code-block:: html+django

    <img src="{{ user.email|gravatar:"24" }}>

Any paramter can be left out to retain its default value. Eg, specifying
default without touching default size or rating:

.. code-block:: html+django

    <img src="{{ user.email|gravatar:"::monsterid" }}>

