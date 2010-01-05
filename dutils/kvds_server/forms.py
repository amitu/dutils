from django import forms

# StoreValue # {{{
class StoreValue(forms.Form):
    key = forms.CharField(max_length=100)
    value = forms.CharField(widget=forms.Textarea)

    def save(self, backend):
        d = self.cleaned_data.get
        backend.set(str(d("key")), str(d("value").encode("utf-8")))
        return "/?key=%s" % d("key")
# }}}
