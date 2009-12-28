from django.http import HttpResponse, Http404

def get_response(request):
    if request.path.startswith("/blog"):
        return HttpResponse(request.path)
    raise Http404

if __name__ == "__main__":
    import pld, set_paths, path
    APP_DIR=path.path(__file__).parent.abspath()
    pld.handle(
        INSTALLED_APPS=["dutils"], DEBUG=True,
        ROOT_URLCONF="dutils.kvds_server.urls", APP_DIR=APP_DIR,
    )
    pld.handle(
        get_response=get_response, INSTALLED_APPS=["dutils"], DEBUG=True,
        ROOT_URLCONF="dutils.kvds_server.urls", APP_DIR=APP_DIR,
    )
