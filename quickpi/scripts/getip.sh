#!/bin/bash

/sbin/ifconfig $1 | grep 'inet ' | tr -s ' ' | cut -d" " -f3
