from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Write what stood out, what worked, or who you would recommend it to...",
                }
            )
        }
