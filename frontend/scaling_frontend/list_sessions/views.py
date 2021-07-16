from django.shortcuts import render
import requests

from lib.variables import list_url, del_url


def get_list_sessions(type="active", url=list_url):
    params = {"session_type": "active"}
    try:
        r = requests.get(url=url, params=params)
        data = r.json()
        if type in data.keys() and len(data[type]) > 0:
            return data[type]
        else:
            return "no_data"
    except requests.exceptions.RequestException:
        return "connection_error"


def del_session(session_id, url=del_url):
    params = {"session_id": session_id}
    try:
        r = requests.delete(url=url, params=params)
        data = r.json()
        return data
    except requests.exceptions.RequestException:
        return "connection_error"


# Create your views here.
def list_sessions_view(request, *args, **kwargs):
    print(request.POST.get("action"))
    data = get_list_sessions()
    if request.method == 'POST':
        if request.POST.get('action') != None:
            if request.POST.get('action') == 'Delete':
                del_session(request.POST.get("session_id"))
        # TODO: need to handle connection errors
        data = get_list_sessions()
    dict = {
        "example": "example",
        "data": data
    }
    return render(request, "list_sessions.html", dict)
