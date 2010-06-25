Form Handler
************

.. include:: global.rst

`dutils.utils.form_handler` is a generic view that can be used for handling forms.

.. function:: dutils.utils.form_handler(request, form_cls, require_login=False, block_get=False, next=None, template=None, login_url=None, pass_request=True)

    Some ajax heavy apps require a lot of views that are merely a wrapper
    around the form. This generic view can be used for them.

    :param request: request object, instance of HttpRequest_
    :param form_cls: form class to use
    :type form_cls: string or instance of Form_ subclass.
    :param require_login: boolean or callable, if this is true, use must login before they can interact with the form
    :param block_get: if true, GET requests are not allowed.
    :param next: if passed, user will be redirected to this url after success
    :param template: if passed, this template will be used to render form
    :param login_url: user will be redirected to this user if login is required
    :param pass_request: form instance would be created with request as first parameter if this is true
    :rtype: instance of HttpResponse_ subclass

Use Cases
=========

`form_handler` can be used in various scenarios.

Simple Form Handling
--------------------

A typical form handler in django is the following view::

    from myproj.myapp.forms import MyApp

    def my_form_view(request):
        if request.method == "POST":
            form = MyForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect("/somewhere/")
        else:
            form = MyForm()
        return render_to_response(
            "my_form.html", { "form": form }, context_instance=RequestContext(request)
        )

This can be handled by `form_handler` by putting the following entries in urls.py::

    from django.conf.urls.defaults import *

    urlpatterns = patterns('',
        url(r'^my-form/$',
           "dutils.utils.form_handler",
           {
               'template': 'my_form.html',
               "form_cls": "myproj.myapp.forms.MyForm",
               "next": "/somewhere/",
           },
        ),
    )

The URL to be redirected is variable
------------------------------------

Sometimes when lets say you created a new object, and user should be redirected
to that object, instead of a static url, `next` parameter is not suffecient. In
such cases, do not pass `next` and let form.save() return the URL.
`form_handler` will redirect user to this url.::

    class CreateBookForm(forms.Form):
        title = forms.CharField(max_length=50)

        def save(self):
            book = Book.objects.create(title=title)
            return book.get_absolute_url()

    urlpatterns = patterns('',
        url(r'^create-book/$',
           "dutils.utils.form_handler",
           {
               'template': 'create-book.html',
               "form_cls": CreateBookForm,
               "pass_request": False,
           },
        ),
    )

Access to request parameters required
-------------------------------------

Sometimes for valid form processing, some aspect of request has to be know. In
this case make sure your Form can take request as the first parameter, and set
`pass_request` to `True`.::


    class CreateBookForm(forms.Form):
        title = forms.CharField(max_length=50)

        def __init__(self, request, *args, **kw):
            super(CreateBookForm, self).__init__(*args, **kw)
            self.request = request

        def save(self):
            book = Book.objects.create(title=title, user=self.request.user)
            return book.get_absolute_url()

    urlpatterns = patterns('',
        url(r'^create-book/$',
           "dutils.utils.form_handler",
           {
               'template': 'create-book.html',
               "form_cls": CreateBookForm,
               "pass_request": True,
               "require_login": True,
           },
        ),
    )


|utils| comes with a utility class derived from Form_ known as `RequestForm`.
This form takes care of storing the request passed in constructor, so the above
form can be re written as::

    class CreateBookForm(dutils.utils.RequestForm):
        title = forms.CharField(max_length=50)

        def save(self):
            book = Book.objects.create(title=title, user=self.request.user)
            return book.get_absolute_url()

    urlpatterns = patterns('',
        url(r'^create-book/$',
           "dutils.utils.form_handler",
           {
               'template': 'create-book.html',
               "form_cls": CreateBookForm,
               "require_login": True,
           },
        ),
    )

.. note:: since `pass_request` is `True` by default this can be omitted. 

Only users with valid account can access the form
-------------------------------------------------

Sometimes being logged in is not enough, you may want users to satisfy some
kind of condition before they can access the form, for example they account if
valid, or it has enough balance or whatever.

This can be achieved by a combination of `require_login` and `login_url`. Lets
say our user object has can_create_books() method on its UserProfile.

Also lets assume that "/make-payment/" is the URL user will go to if they do
not have permission to create books.

Here is how to handle this situation::

    def can_create_books(request):
        if not request.user.is_authenticated(): return False
        return request.user.get_profile().can_create_books()

    urlpatterns = patterns('',
        url(r'^create-book/$',
           "dutils.utils.form_handler",
           {
               'template': 'create-book.html',
               "form_cls": CreateBookForm,
               "require_login": can_create_books,
               "login_url": "/make-payment/",
           },
        ),
    )

.. note:: 

    `require_login` can be a callable. If its a callable, it will be passed
    request as the first parameter.

Doing Ajax
----------

Lets say we want to export all this as ajax. You actually don't have to do
anything, just pass "json=true" as a REQUEST parameter.

The form will return JSON objects, with parameter `success` which is `true` or
`false`.

If its `true` when everything goes well, in this case, it will contain
`response` parameter, which will be JSON encoded value of whatever was returned
by the `form.save()`.

`success` is `false` if there was some form validation error, or if redirect is
required. If redirect is required when conditions are not met, JSON contains a
parameter `redirect` which contains the URL to which user has to be redirected.

If `success` is `false` because of form validation errors, a property `errors`
contains JSON encoded error messages.

