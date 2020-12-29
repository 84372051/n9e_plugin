#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Yang'

import socket
import time
import json
import threadpool

hostname=socket.gethostname()

Entry = {
        "Endpoint": hostname,
        "Timestamp": int(time.time()),
        "Step": 60,
    }

#端口超时时间默认设置为5秒
def check_tcp_port(kw, timeout=5):
    try:
        cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = (str(kw["host"]), int(kw["port"]))
        cs.settimeout(timeout)
        status = cs.connect_ex(address)
        cs.close()
    except Exception as e:
        return {"status": False, "message": str(e)}
    else:
        if status != 0:
            return {"status": False, "message": "Connection %s:%s failed" % (kw["host"], kw["port"])}
        else:
            return {"status": True, "message": "OK"}

def run_check(entry_list,host,port,metric_type):
    kw={"host": host,"port": port}
    status=check_tcp_port(kw=kw)
    if status['status'] == True:
        value=1
    else:
        value=0
    entry = Entry.copy()
    entry.update({
        "CounterType": "GAUGE",
        "Metric": "tcp.status",
        "TAGS": "type={0},port={1}".format(host,port),
        "Value": value
    })
    entry_list.append(entry)

def run_threadpool():
    args=[]
    #线程池预设为8，可以根据机器性能修改
    task_pool=threadpool.ThreadPool(8)
    for service in service_list:
        for host in service['ip']:
            args.append(([entry_list,host,service["port"],service["name"]],None))
    
    theads=threadpool.makeRequests(run_check,args)
    [task_pool.putRequest(req) for req in theads ]
    task_pool.wait()
    

if __name__ == '__main__':
    entry_list = []
    service_list=[]
    #添加服务就按照下面的例子给service_list添加一个dict,
    service_list.append({ 
                    "name": "zookeeper" ,
                    "ip": ["192.168.1.100","192.168.1.101","192.168.1.102"],
                    "port": "2181"
                })
    
    service_list.append({
                    "name": "rabbitmq" ,
                    "ip": ["192.168.1.103","192.168.1.104","192.168.1.105"],
                    "port": "5672"
                    })

    run_threadpool()
    print(json.dumps(entry_list))
