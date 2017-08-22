# This is the default config that ships with the Docker image with the
# addition of the logic to save .html and .py versions of the notebooks

from jupyter_core.paths import jupyter_data_dir
from subprocess import check_call

import subprocess
import os
import errno
import stat

PEM_FILE = os.path.join(jupyter_data_dir(), 'notebook.pem')

c = get_config()
c.NotebookApp.ip = '*'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False

# Set a certificate if USE_HTTPS is set to any value
if 'USE_HTTPS' in os.environ:
    if not os.path.isfile(PEM_FILE):
        # Ensure PEM_FILE directory exists
        dir_name = os.path.dirname(PEM_FILE)
        try:
            os.makedirs(dir_name)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
                pass
            else: raise
        # Generate a certificate if one doesn't exist on disk
        subprocess.check_call(['openssl', 'req', '-new',
            '-newkey', 'rsa:2048', '-days', '365', '-nodes', '-x509',
            '-subj', '/C=XX/ST=XX/L=XX/O=generated/CN=generated',
            '-keyout', PEM_FILE, '-out', PEM_FILE])
        # Restrict access to PEM_FILE
        os.chmod(PEM_FILE, stat.S_IRUSR | stat.S_IWUSR)
    c.NotebookApp.certfile = PEM_FILE

# Disable authentication altogether, NOT RECOMMENDED FOR PRODUCTION ENVIRONMENTS
c.NotebookApp.token = ''

### If you want to auto-save .html and .py versions of your notebook:
# modified from: https://github.com/ipython/ipython/issues/8009
def post_save(model, os_path, contents_manager):
    """post-save hook for converting notebooks to .py scripts"""
    if model['type'] != 'notebook':
        return # only do this for notebooks
    d, fname = os.path.split(os_path)
    check_call(['jupyter', 'nbconvert', '--to', 'script', fname], cwd=d)
    check_call(['jupyter', 'nbconvert', '--to', 'html', fname], cwd=d)
c.FileContentsManager.post_save_hook = post_save
