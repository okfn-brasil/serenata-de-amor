import configparser
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

files = set(name for name in os.listdir('data') if not name.startswith('.'))
files_in_bucket = set(attrs['key'] for attrs in connection.list(None, bucket))
for filename in (files - files_in_bucket):
    filepath = 'data/' + filename
    print(filepath)
    connection.upload(filename, open(filepath, 'rb'))
