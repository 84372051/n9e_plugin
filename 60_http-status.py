#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import json
import requests
import socket

local_port='8080'
hostname=socket.gethostname()
if hostname.find('eureka') >=0:
    local_port='7018'

Entry = {
        "Endpoint": hostname,
        "Timestamp": int(time.time()),
        "Step": 60,
    }


def check_local(entry_list,port):
    url= "http://"+hostname+":"+port
    try:
        http_status=requests.get(url,allow_redirects=False,timeout=10).status_code
    except Exception, e:
        http_status=0

    entry = Entry.copy()
    entry.update({
            "CounterType": "GAUGE",
            "Metric": "http.status",
            "TAGS": "",
            "Value": http_status
        })
    entry_list.append(entry)


if __name__ == '__main__':
    entry_list=[]
    check_local(entry_list=entry_list,port=local_port)
    print(json.dumps(entry_list))
