@echo off
set PGPASSWORD=Mmsucit1502
psql -h 192.168.10.42 -U postgres -c "DROP DATABASE IF EXISTS funtime_tbl;"
psql -h 192.168.10.42 -U postgres -c "CREATE DATABASE funtime_tbl;"
echo Database reset successfully
