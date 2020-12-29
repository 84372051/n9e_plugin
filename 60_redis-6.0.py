#!/bin/env python
# -*- coding:utf-8 -*-

import os
import time
import json
import redis
import socket
import re




Entry = {
    "Endpoint": socket.gethostname(),
    "Timestamp": int(time.time()),
    "Step": 60,
}


def redis_metric(result, port, pw):
    def guage(metric, value):
        res = Entry.copy()
        res.update({
            "CounterType": "GAUGE",
            "Metric": "redis.{0}".format(metric),
            "TAGS": "type=redis,port={0}".format(port),
            "Value": value
        })
        return res

    def counter(metric, value):
        res = Entry.copy()
        res.update({
            "CounterType": "COUNTER",
            "Metric": "redis.{0}".format(metric),
            "TAGS": "type=redis,port={0}".format(port),
            "Value": value
        })
        return res

    try:
        r = redis.StrictRedis(host='localhost', port=port, password=pw)
        info = r.info()
    except redis.exceptions.ResponseError:
	#print(port,pw)
        r = redis.StrictRedis(host='localhost', port=port)
        info = r.info()

    # clients
    connected_clients = int(info['connected_clients'])
    connected_clients_pct = float(info['connected_clients']) / int(r.config_get('maxclients')['maxclients']) * 100
    client_biggest_input_buf = int(info['client_recent_max_input_buffer'])
    result.append(guage('client_recent_max_input_buffer',client_biggest_input_buf))
    result.append(guage('connected_clients', connected_clients))
    result.append(guage('connected_clients_pct', connected_clients_pct))

    # memory
    used_memory = int(info['used_memory'])
    used_memory_pct = float(used_memory) / int(info['maxmemory']) * 100
    mem_fragmentation_ratio = info['mem_fragmentation_ratio']
    result.append(guage('used_memory', used_memory))
    result.append(guage('used_memory_pct', used_memory_pct))
    result.append(guage('mem_fragmentation_ratio', mem_fragmentation_ratio))
    
    # hit
    keyspace_hits = int(info['keyspace_hits'])
    keyspace_misses = int(info['keyspace_misses'])
    keyspace_total = keyspace_hits + keyspace_misses
    if keyspace_total == 0:
        keyspace_hit_ratio = 0
    else:
        keyspace_hit_ratio = float(keyspace_hits) / (keyspace_hits + keyspace_misses) * 100
    result.append(guage('keyspace_hits', keyspace_hits))
    result.append(guage('keyspace_hit_ratio', keyspace_hit_ratio))

    # network
    result.append(guage('instantaneous_input_kbps', info['instantaneous_input_kbps']))
    result.append(guage('instantaneous_output_kbps', info['instantaneous_output_kbps']))

    # commands
    result.append(guage('instantaneous_ops_per_sec', info['instantaneous_ops_per_sec']))
    result.append(counter('total_commands_processed', info['total_commands_processed']))

    # save
    rdb_last_bgsave_status = 1 if info['rdb_last_bgsave_status'] == 'ok' else 0
    aof_last_bgrewrite_status = 1 if info["aof_last_bgrewrite_status"] == 'ok' else 0
    aof_last_write_status = 1 if info["aof_last_write_status"] == 'ok' else 0
    result.append(guage('rdb_last_bgsave_status', rdb_last_bgsave_status))
    result.append(guage('aof_last_bgrewrite_status', aof_last_bgrewrite_status))
    result.append(guage('aof_last_write_status', aof_last_write_status))

    # repl
    role = info['role']
    if role == 'slave':
        master_link_status = 1 if info['master_link_status'] == 'up' else 0
        result.append(guage('master_link_status', master_link_status))
        result.append(guage('master_status', 0))
    else:
        result.append(guage('master_status', 1))


if __name__ == "__main__":
    result = []
    pw = ''
    for f in os.listdir('/etc/redis'):

        rerz = re.findall('redis-(\d+).conf$', f)
        file = '/etc/redis/' + f
        if os.path.isfile(file):
            with open(file) as ff:
                for line in ff.readlines():
                    if line.startswith('requirepass'):
                        pw = line.split()[1].strip('"')
        if rerz:
            port = rerz[0]
	    #print(port)
            redis_metric(result, port, pw)
    res = Entry.copy()
    res.update({
            "CounterType": "GAUGE",
            "Metric": "redis.{0}".format('plugin.alive'),
            "TAGS": "",
            "Value": 1
        })

    result.append(res)
    print(json.dumps(result))
