from dutils import utils
from datetime import datetime

@utils.templated("time.html")
def handle(request):
    return { "d": datetime.now() }
