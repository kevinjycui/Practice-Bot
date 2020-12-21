#!/bin/bash

pid=$(ps -a | grep python3 | awk '{print $1}')

if [[ -z $pid ]]
then
    echo Error! No process found.
    exit 1
fi

echo %CPU %MEM

while [[ ! -z $(ps -a | grep python3) ]]
do
    ps -p $pid -o %cpu,%mem | sed -n 2p
    sleep 1
done

echo Terminated!
