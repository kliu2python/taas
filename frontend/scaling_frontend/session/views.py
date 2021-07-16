from django.shortcuts import render


# Create your views here.
def contact_view(request, *args, **kwargs):
    contact_dict = {}
    return render(request, "contact.html", contact_dict)


def session_view(request, *args, **kwargs):
    about_dict = {}
    return render(request, "session.html", about_dict)
