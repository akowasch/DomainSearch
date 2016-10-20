#!/bin/bash

ACTION="$1"
USER="$2"
PASSWORD="$3"
DATABASE="$4"
 
if [ $# -ne 4 ]; then

	echo "Usage: $0 {Action} {MySQL-User-Name} {MySQL-User-Password} {MySQL-Database-Name}"
	echo "Action = drop : Drops all tables from from the given Database"
	echo "Action = truncate : Truncates all tables from the given Database"
	exit 1
fi

if [ $1 = "drop" ]; then

	TABLES=$(mysql -u $USER -p$PASSWORD $DATABASE -e 'show tables' | awk '{ print $1}' | grep -v '^Tables' )

	for t in $TABLES; do
		echo "Deleting $t table from $DATABASE database."
		mysql -u $USER -p$PASSWORD $DATABASE -e "drop table $t"
	done

elif [ $1 = "truncate" ]; then

	TABLES=$(mysql -u $USER -p$PASSWORD $DATABASE -e 'show tables' | awk '{ print $1}' | grep -v '^Tables' )

	for t in $TABLES; do
		echo "Clearing $t table from $DATABASE database."
		mysql -u $USER -p$PASSWORD $DATABASE -e "truncate table $t"
	done

else

	echo "Usage: $0 {Action} {MySQL-User-Name} {MySQL-User-Password} {MySQL-Database-Name}"
	echo "Action = drop : Drops all tables from from the given Database"
	echo "Action = truncate : Truncates all tables from the given Database"
	exit 1
fi
