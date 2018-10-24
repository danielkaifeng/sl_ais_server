ps -aux|grep sl_server|grep -v grep|awk '{print $2}'|xargs -i kill -9 {}
nohup python sl_server.py runserver --processes 12  1>o.log 2>e.log &
