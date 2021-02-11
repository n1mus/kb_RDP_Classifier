#!/bin/bash


cd /data 
gdown https://drive.google.com/uc?id=15tdT7_hJV8lOCpLX1-IfKw7w1IwKn21Z
tar xzf /data/refdata.gz
touch /data/__READY__
