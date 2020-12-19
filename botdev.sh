#!/bin/bash

if [[ $VIRTUAL_ENV == "" ]]
then
    . env/bin/activate
fi

python3 bot.py