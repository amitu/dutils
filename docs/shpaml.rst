SHPAML Template Loader
**********************

.. include:: global.rst

|dutils| comes with a custom template loader for working with SHPAML_ templates.

.. note::

    |dutils| bundles SHPAML, so there is no need to install anything to user
    this feature.

What is SHPAML
--------------

From their `webpage <http://shpaml.webfactional.com/>`_::

    SHPAML is a mini language that can help you to build web pages more
    quickly. It leverages familiar concepts from HTML and CSS, while striving
    to bring brevity and clarity to the primary documents that you edit. It
    plays nice with templating languages.

Input::

    div.free_text
      This is some text.

    ul class="list_of_names"
      li | Alice
      li | Bob
      li | Cindy

    div.class1.class2
      You can have multiple classes.

Output:

.. code-block:: html

    <div class="free_text">
      This is some text.
    </div>

    <ul class="list_of_names">
      <li>Alice</li>
      <li>Bob</li>
      <li>Cindy</li>
    </ul>

    <div class="class1 class2">
      You can have multiple classes.
    </div>

More examples available on their webiste: SHPAML_.

Using SHPAML Template Loader
----------------------------

`dutils.shpaml_loader` defines a template loader, that looks for shpaml
templates in directories specified in `settings.SHPAML_TEMPLATE_DIRS`.

Put the following in your settings.py to use shpaml_loader::

    SHPAML_TEMPLATE_DIRS = (
        "/Users/amitupadhyay/projects/projs/dutils/shpaml_templates/",
    )

    TEMPLATE_LOADERS = (
        'dutils.shpaml_loader.load_template_source',
        'django.template.loaders.filesystem.load_template_source',
        'django.template.loaders.app_directories.load_template_source',
    )

Using `dutils.shpaml` Command Line Tool
---------------------------------------

Another option is to generate HTML from SHPAML using `dutils.shpaml` module:

.. code-block:: sh

    $ python -m dutils.shpaml sh.html
    <div class="free_text">
        This is some text.
    </div>

    <ul class="list_of_names">
        <li>Alice</li>
        <li>Bob</li>
        <li>Cindy</li>
    </ul>

    <div class="class1 class2">
        You can have multiple classes.
    </div>

The output can be redirected to a file, that can then be used by django to
server.

