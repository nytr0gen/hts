#!/bin/bash

(python ./app/updatedb.py > ./update.log) &

python ./app/app.py
