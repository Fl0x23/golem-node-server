from flask import Flask, request
from flask_httpauth import HTTPTokenAuth
from golem import GolemStatus
from flask_cors import CORS
import secrets
import hardware
import sys
import subprocess as sp

app = Flask(__name__)

CORS(app, resources=r'/api/*')

auth = HTTPTokenAuth(scheme='Bearer')
tokens = { 'V22PFvsrRcUf9j1ktipL_A': 'admin' }

def set_settings(settings):
    return sp.Popen(["golemsp", "settings", "set"] + settings, stdout=sp.PIPE).communicate()[0].decode('utf-8')

def generate_HTTPTokenAuth():
    if sum(len(token) for token in tokens) == 0:
        secret = secrets.token_urlsafe(16)
        tokens[secret] = "admin"
        return " + Random_HTTPTokenAuth: " + str(tokens)
    else:
        return " + HTTPTokenAuth: " + str(tokens)

def settings_stats(status):
    return {  
        "shared": {
            "cpu_threads": status.cpu_threads(),
            "mem_gib": status.mem_gib(),
            "storage_gib": status.storage_gib(),
        },
        "pricing": {
            "for_start": status.price_for_start(),
            "env_per_hour": status.price_env_per_hour(),
            "cpu_per_hour": status.price_cpu_per_hour(),
        }
    }

def hardware_stats():
    return {
        "cpu": hardware.cpu(),
        "memory": hardware.memory(),
        "isProcessingTask": hardware.isProcessingTask(),
    }

def current_time():
    # return : current time in millis
    import calendar
    import time
    return calendar.timegm(time.gmtime())

def golem(status):
    return {
        "name": status.node_name(),
        "id": status.id(),
        "version": status.version(),
        "update": status.update(),
        "wallet": status.account(),
        "network": status.network(),
        "subnet": status.subnet(),
        "processedTotal": status.processed_total(),
        "processedLastHour": status.processed_hour(),
    }

@auth.verify_token
def verify_token(token):
    if token in tokens:
        return tokens[token]

@app.route('/api/status', methods=['GET'])
def stats_all():
    golem_status = GolemStatus()
    hardware = hardware_stats()
    hardware.update(settings_stats(golem_status))
    return {
        "timestamp" : current_time(),
        "hardware" : hardware,
        "info": golem(golem_status),
    }

@app.route('/api/settings', methods=['POST'])
@auth.login_required
def settings():
    cmd=[]
    json = request.json
    for key in json:
        cmd.append("--" + key)
        cmd.append(str(json.get(key)))
    set_settings(cmd)
    return stats_all()

if __name__ == '__main__':
    print(generate_HTTPTokenAuth())
    app.run(host='0.0.0.0')
