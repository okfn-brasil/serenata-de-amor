import configparser
import datetime
import os
import tinys3

settings = configparser.RawConfigParser()
settings.read('config.ini')
access_key = settings.get('Amazon', 'AccessKey')
secret_key = settings.get('Amazon', 'SecretKey')
bucket = settings.get('Amazon', 'Bucket')
region = settings.get('Amazon', 'Region')

connection = tinys3.Connection(access_key,
                               secret_key,
                               default_bucket=bucket,
                               endpoint='%s.amazonaws.com' % region)

date = datetime.datetime.utcnow().isoformat()[:10]
files = [name for name in os.listdir('data') if not name.startswith('.')]
for filename in files:
    backup_filename = '%s-%s' % (date, filename)
    connection.upload(backup_filename, open('data/' + filename, 'rb'))
