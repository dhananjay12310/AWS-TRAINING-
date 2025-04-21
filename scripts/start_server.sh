#!/bin/bash
cd /home/ec2-user/app
export FLASK_APP=application.py
gunicorn --bind 0.0.0.0:5000 application:app --daemon
