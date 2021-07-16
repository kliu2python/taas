from django import forms


class RequestForm(forms.Form):
    session_id = forms.CharField(label="Session ID", max_length=20)
    host_ip = forms.CharField(label="Host IP", max_length=20,
                              initial="172.30.156.103")
    username = forms.CharField(label="User Name", max_length=20,
                               initial="admin")
    password = forms.CharField(label="Password", max_length=20, required=False)
    target_host_ip = forms.CharField(label="Target Host IP", max_length=20,
                                     initial="172.30.156.103")
    target_platform = forms.ChoiceField(label="Target Platform (ftc or fis)",
                                        choices=[("fil", "FortiIsolator"),
                                                 ("ftc", "FTC")],
                                        initial="FIS")
    runner_count = forms.CharField(label="Runner Count", max_length=20)
    loop = forms.BooleanField(required=False, initial=True)
    wait_seconds_after_notify = forms.FloatField(label="Wait this many seconds "
                                                       "after notify",
                                                 initial=20)
    deployment_config = forms.CharField(label="Deployment Config File",
                                        initial="runner_deployment_fis.yaml")
    pods_adjust_momentum = forms.IntegerField(label="Pods adjust momentum",
                                              initial=1)
    force_new_session = forms.BooleanField(required=False)
