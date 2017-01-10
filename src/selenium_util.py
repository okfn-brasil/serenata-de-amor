import os
import platform
import requests
import tempfile
import zipfile
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException


# Download, unzip and use the correct Selenium Web Driver accordingly with operational system and Browser
# Chrome, Firefox and Opera supported
def webdriver_from_system():
    webdrivers = {
        'linux_32bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_linux32.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver.exe',
                'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-linux32.tar.gz',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver', 'object': webdriver.Firefox
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_linux32.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver', 'object': webdriver.Opera
            }
        ],
        'linux_64bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_linux64.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver', 'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_linux64.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver', 'object': webdriver.Opera
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-linux64.tar.gz',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver', 'object': webdriver.Firefox
            }
        ],
        'Darwin_64bit': [
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_mac64.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver', 'object': webdriver.Opera
            },
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_mac64.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver', 'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-macos.tar.gz',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver', 'object': webdriver.Firefox
            }
        ],
        'Windows_32bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_win32.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver.exe',
                'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-win32.zip',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver.exe', 'object': webdriver.Firefox
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_win32.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver.exe', 'object': webdriver.Opera
            }
        ],
        'Windows_64bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_win32.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver.exe', 'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-win64.zip',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver.exe', 'object': webdriver.Firefox
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_win64.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver.exe', 'object': webdriver.Opera
            }
        ]
    }

    platform_name = '%s_%s' % (platform.system(), platform.architecture()[0])
    assert platform_name in webdrivers, 'Your platform is not compatible with Selenium WebDrivers supported'
    driver_list = webdrivers[platform_name]

    for driver_info in driver_list:
        try:
            executable_path = os.path.abspath(driver_info['file_name'])
            if not os.path.exists(executable_path):
                r = requests.get(driver_info['url'])
                if r.status_code == 200:
                    f = tempfile.NamedTemporaryFile(mode='wb', delete=False)
                    f.write(r.content)
                    f.close()

                    z = zipfile.ZipFile(f.name)
                    z.extract(driver_info['file_name'])
                    z.close()
                    os.remove(f.name)

            if os.path.exists(executable_path):
                try:
                    return driver_info['object'](executable_path=executable_path,
                                                 desired_capabilities=driver_info['capabilities'])
                except TypeError:
                    # In some browsers the name of param 'desired_capabilities' is different it's 'capabilities'
                    return driver_info['object'](executable_path=executable_path,
                                                 capabilities=driver_info['capabilities'])
        except WebDriverException:
            pass
