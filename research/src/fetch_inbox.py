import configparser
import datetime
import dateutil.parser
import email
import imaplib
import os
import quopri
import re
import sys
import unicodedata


def normalize_string(string):
    if isinstance(string, bytes):
        string = string.decode('utf-8', 'replace')
    if isinstance(string, str):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')

settings = configparser.RawConfigParser()
settings.read('config.ini')
EMAIL_ACCOUNT = 'op.serenatadeamor@gmail.com'
EMAIL_PASSWORD = settings.get('Email', 'Password')
EMAIL_FOLDER = '"{}"'.format(sys.argv[1])
EMAIL_REGEX = r'op\.serenatadeamor?\+(\w+)@gmail\.com'
PATH = os.path.join('data/email_inbox', EMAIL_FOLDER[1:-1])



M = imaplib.IMAP4_SSL('imap.gmail.com')
rv, data = M.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
rv, mailboxes = M.list()
rv, data = M.select(EMAIL_FOLDER)
rv, data = M.search(None, 'ALL')

for code in data[0].split():
    rv, data = M.fetch(code, '(RFC822)')
    message = email.message_from_bytes(data[0][1])
    body = quopri.decodestring(str(message))
    date = dateutil.parser.parse(message['Date']) \
        .astimezone(datetime.timezone.utc).isoformat()[:-6]
    subject = email.header.decode_header(message['Subject'])[0][0]
    subject = normalize_string(subject)
    filename = re.sub(r'[:\+\. ]', '_', '{} {}'.format(date, subject))
    mailpath = os.path.join(PATH, filename)
    mailtextpath = os.path.join(mailpath, 'message.txt')

    if os.path.exists(mailpath):
        continue

    os.makedirs(mailpath)

    with open(mailtextpath, 'w') as file_:
        file_.write(body.decode('utf-8', 'replace'))
    if message.get_content_maintype() == 'multipart':
        for part in message.walk():
            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                attachmentpath = os.path.join(mailpath, part.get_filename())
                open(attachmentpath, 'wb').write(part.get_payload(decode=True))
