#!/bin/bash

/sbin/ifconfig $1 | grep 'ether ' | tr -s ' ' | cut -d" " -f3
