#!/bin/bash

curl -s http://192.168.0.1:5000/run_5 &
curl -s http://192.168.0.2:5000/run_5 &
curl -s http://192.168.0.3:5000/run_5 &
curl -s http://192.168.0.4:5000/run_5 &
curl -s http://192.168.0.5:5000/run_5
