New in Development
==================

* Create ChangeLog file.
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
  <http://packages.python.org/dutils/form_handler.html#doing-ajax>`_.

New in 0.0.7
============

* Created fabfile to push both zip and tar.gz releases. fabfile simultaneously
  compiles and uploads docs.

