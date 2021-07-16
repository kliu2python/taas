# Rest API Services 

Device Manager Launch commands
export ANDROID_HOME=/home/fortinet/Android/Sdk
cd /home/fortinet/git/pytest-automation/tools/test_assistant_rest_api || exit
ps -ef | grep "app.py" | grep -v grep | awk '{print $2}' | xargs kill -9
/home/fortinet/anaconda3/envs/py38/bin/python app.py &
