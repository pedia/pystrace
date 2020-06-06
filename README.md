strace 日志分析

python 2.6 下必须安装 counter
```bash 
pip install counter
```

# 必须采用以下参数:  
strace -f -s 1024 -T -ttt

## 通常trace所有api uwsgi采用以下脚步
```bash
ps aufx | grep uwsgi| grep /api/ | awk '{print $2}' > pids
for i in `cat pids`; do echo strace -f -p $i -s 1024 -T -ttt -o strace.$i.log \&; done > a.sh
```

## pkill strace 后，可以看分析结果
```bash
cat *.log | python strace2an.py
```