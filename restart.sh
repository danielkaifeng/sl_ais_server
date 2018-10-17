ps -aux|grep ais|grep -v grep|awk '{print $2}'|xargs -i kill -9 {}
nohup python ais_server.py runserver --processes 12  1>o.log 2>e.log &
