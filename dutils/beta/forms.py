from django import forms

from dutils.utils import RequestForm
from dutils.beta.models import BetaRequest

class CreateRequest(RequestForm):
    email = forms.EmailField()

    def save(self):
        BetaRequest.objects.create_beta_request(self.cleaned_data["email"])

class LetMeIn(RequestForm):
    code = forms.CharField(max_length=32, min_length=32)

    def init(self):
        code = request.REQUEST.get("code")
        if not code or not code_is_fine(code): return
        return self.drop_cookie(code)

    def code_is_fine(self, code):
        try:
            BetaRequest.objects.get(code=code, approved=True)
        except BetaRequest.DoesNotExist:
            return False
        return True

    def drop_cookie(self, code):
        response = HttpResponseRedirect("/")
        response.set_cookie("dbeta", code, max_age=3600*24*365)
        return response

    def clean_code(self):
        code = self.cleaned_data["code"]
        if not self.code_is_fine(code):
            raise forms.ValidationError("Invalid Code.")
        return code

    def save(self):
        return self.drop_cookie(self.cleaned_data["code"])

class Allow(RequestForm):
    code = forms.CharField(max_length=32, min_length=32)

    def code_is_fine(self, code):
        try:
            self.br = BetaRequest.objects.get(code=code, approved=False)
        except BetaRequest.DoesNotExist:
            return False
        return True

    def clean_code(self):
        code = self.cleaned_data["code"]
        if not self.code_is_fine(code):
            raise forms.ValidationError("Invalid Code.")
        return code

    def save(self):
        self.br.approve(self.request.user)
        return HttpResponse("Approved, sent mail to %s" % self.br.email)


