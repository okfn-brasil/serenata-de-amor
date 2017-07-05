echo "alias m=\"$VIRTUAL_ENV/bin/python $(pwd)/manage.py\"" >> $VIRTUAL_ENV/bin/postactivate
echo "unalias m" >> $VIRTUAL_ENV/bin/postdeactivate
