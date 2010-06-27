Install latest development version to get these features::

    sudo easy_install -U http://github.com/amitu/dutils/tarball/master

New in Development
==================

* Better handling of initial values of form fields in get_form_representation().
* Merged changes done in http://github.com/dwiel/threadpool
* Added a new app, `dutils.reg`, which will eventually be a replacement for
  `django-registration` app.
* Added dutils.reg.views.resend_confirmation_code view.

New in 0.0.9
============

* Added a try_del(dict, \*keys_to_remove) method, removes all keys if they are
  there in the passed dict.
* Minor bug fix in get_form_representation, label is not always present.
* .get_json() is better name than .get_ajax(), changed that.

New in 0.0.8
============

* Created ChangeLog file.
* Updated docs to point to ChangeLog file.
* Added `validation_only feature
  <http://packages.python.org/dutils/form_handler.html#as-you-type-ajax-validation>`_
  to form_handler.
* Fixed a bug in form_handler, error messages were not getting displayed in
  forms.
* If a form is set for both ajax and for normal usage, implicitly calling
  json.dumps on returned object of form.save() can be limiting, sometimes that
  contains the redirect url, only meaningful for normal web access. Added a
  lookup for form.get_ajax(), that when present can be used to fix this issue.
  `Read docs
  <http://packages.python.org/dutils/form_handler.html#using-same-form-for-json-access-and-normal-web-access>`_.
* If is_ajax is true for form_handler, a GET request leads to a JSON
  representation of form.
* form_handler can now accept keyword arguments from URL patterns and pass them
  to .init() for forms if .init() is available. `Read docs
  <http://packages.python.org/dutils/form_handler.html#forms-that-take-parameters-from-url>`_.

New in 0.0.7
============

* Created fabfile to push both zip and tar.gz releases. fabfile simultaneously
  compiles and uploads docs.

