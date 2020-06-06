#!/bin/bash
sleep 5
echo flushall |redis-cli -h zoo -p 6379
echo flush_all | nc zoo 11201
cd /data/duyue
ps aufx | grep uwsgi| grep /api/ | awk '{print $2}' > pids
for i in `cat pids`; do echo strace -f -p $i -s 1024 -T -ttt -o strace.$i.log \&; done > a.sh
sh a.sh
sleep 5
source /opt/rh/python27/enable; source /data/www/env/bin/activate;cd /data/www/xx_api/;python test.py api http://api.cutmind.com
pkill strace
cd /data/duyue
content=`cat *.log|python pystrace/strace2an.py`
python /root/duyue/mailtext.py "stage api publish strace 1/2 " "$content"
rm -f *.log a.sh pids
sleep 20
ps aufx | grep uwsgi| grep /api/ | awk '{print $2}' > pids
for i in `cat pids`; do echo strace -f -p $i -s 1024 -T -ttt -o strace.$i.log \&; done > a.sh
sh a.sh
sleep 5
source /opt/rh/python27/enable; source /data/www/env/bin/activate;cd /data/www/xx_api/;python test.py api http://api.cutmind.com
pkill strace
cd /data/duyue
content=`cat *.log|python pystrace/strace2an.py`
python /root/duyue/mailtext.py "stage api publish strace 2/2 " "$content"
rm -f *.log a.sh pids
