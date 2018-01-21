Python Twitter

A Python wrapper around the Twitter API.

By the `Python-Twitter Developers <python-twitter@googlegroups.com>`_

.. image:: https://img.shields.io/pypi/v/python-twitter.svg
    :target: https://pypi.python.org/pypi/python-twitter/
    :alt: Downloads

.. image:: https://readthedocs.org/projects/python-twitter/badge/?version=latest
    :target: http://python-twitter.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://circleci.com/gh/bear/python-twitter.svg?style=svg
    :target: https://circleci.com/gh/bear/python-twitter
    :alt: Circle CI

.. image:: http://codecov.io/github/bear/python-twitter/coverage.svg?branch=master
    :target: http://codecov.io/github/bear/python-twitter
    :alt: Codecov

.. image:: https://requires.io/github/bear/python-twitter/requirements.svg?branch=master
     :target: https://requires.io/github/bear/python-twitter/requirements/?branch=master
     :alt: Requirements Status

.. image:: https://dependencyci.com/github/bear/python-twitter/badge
     :target: https://dependencyci.com/github/bear/python-twitter
     :alt: Dependency Status

============
Introduction
============

This library provides a pure Python interface for the `Twitter API <https://dev.twitter.com/>`_. It works with Python versions from 2.7+ and Python 3.

`Twitter <http://twitter.com>`_ provides a service that allows people to connect via the web, IM, and SMS. Twitter exposes a `web services API <https://dev.twitter.com/overview/documentation>`_ and this library is intended to make it even easier for Python programmers to use.

==========
Installing
==========

You can install python-twitter using::

    $ pip install python-twitter


If you are using python-twitter on Google App Engine, see `more information <GAE.rst>`_ about including 3rd party vendor library dependencies in your App Engine project.


================
Getting the code
================

The code is hosted at https://github.com/bear/python-twitter

Check out the latest development version anonymously with::

    $ git clone git://github.com/bear/python-twitter.git
    $ cd python-twitter

To install dependencies, run either::

	$ make dev

or::

    $ pip install -Ur requirements.testing.txt
    $ pip install -Ur requirements.txt

Note that ```make dev``` will install into your local ```pyenv``` all of the versions needed for test runs using ```tox```.

To install the minimal dependencies for production use (i.e., what is installed
with ``pip install python-twitter``) run::

    $ make env

or::

    $ pip install -Ur requirements.txt

=============
Running Tests
=============
The test suite can be run against a single Python version or against a range of them depending on which Makefile target you select.

Note that tests require ```pip install pytest``` and optionally ```pip install pytest-cov``` (these are included if you have installed dependencies from ```requirements.testing.txt```)

To run the unit tests with a single Python version::

    $ make test

to also run code coverage::

    $ make coverage

To run the unit tests against a set of Python versions::

    $ make tox

=============
Documentation
=============

View the latest python-twitter documentation at
https://python-twitter.readthedocs.io. You can view Twitter's API documentation at: https://dev.twitter.com/overview/documentation

=====
Using
=====

The library provides a Python wrapper around the Twitter API and the Twitter data model. To get started, check out the examples in the examples/ folder or read the documentation at https://python-twitter.readthedocs.io which contains information about getting your authentication keys from Twitter and using the library.

----
Using with Django
----

Additional template tags that expand tweet urls and urlize tweet text. See the django template tags available for use with python-twitter: https://github.com/radzhome/python-twitter-django-tags

------
Models
------

The library utilizes models to represent various data structures returned by Twitter. Those models are:
    * twitter.Category
    * twitter.DirectMessage
    * twitter.Hashtag
    * twitter.List
    * twitter.Media
    * twitter.Status
    * twitter.Trend
    * twitter.Url
    * twitter.User
    * twitter.UserStatus

To read the documentation for any of these models, run::

    $ pydoc twitter.[model]

---
API
---

The API is exposed via the ``twitter.Api`` class.

The python-twitter requires the use of OAuth keys for nearly all operations. As of Twitter's API v1.1, authentication is required for most, if not all, endpoints. Therefore, you will need to register an app with Twitter in order to use this library. Please see the "Getting Started" guide on https://python-twitter.readthedocs.io for a more information.

To generate an Access Token you have to pick what type of access your application requires and then do one of the following:

- `Generate a token to access your own account <https://dev.twitter.com/oauth/overview/application-owner-access-tokens>`_
- `Generate a pin-based token <https://dev.twitter.com/oauth/pin-based>`_
- use the helper script `get_access_token.py <https://github.com/bear/python-twitter/blob/master/get_access_token.py>`_

For full details see the `Twitter OAuth Overview <https://dev.twitter.com/oauth/overview>`_

To create an instance of the ``twitter.Api`` with login credentials (Twitter now requires an OAuth Access Token for all API calls)::

    >>> import twitter
    >>> api = twitter.Api(consumer_key='consumer_key',
                          consumer_secret='consumer_secret',
                          access_token_key='access_token',
                          access_token_secret='access_token_secret')

To see if your credentials are successful::

    >>> print(api.VerifyCredentials())
    {"id": 16133, "location": "Philadelphia", "name": "bear"}

**NOTE**: much more than the small sample given here will print

To fetch a single user's public status messages, where ``user`` is a Twitter user's screen name::

    >>> statuses = api.GetUserTimeline(screen_name=user)
    >>> print([s.text for s in statuses])

To fetch a list a user's friends::

    >>> users = api.GetFriends()
    >>> print([u.name for u in users])

To post a Twitter status message::

    >>> status = api.PostUpdate('I love python-twitter!')
    >>> print(status.text)
    I love python-twitter!

There are many more API methods, to read the full API documentation either
check out the documentation on `readthedocs
<https://python-twitter.readthedocs.io>`_, build the documentation locally
with::

    $ make docs

or check out the inline documentation with::

    $ pydoc twitter.Api

----
Todo
----

Patches, pull requests, and bug reports are `welcome <https://github.com/bear/python-twitter/issues/new>`_, just please keep the style consistent with the original source.

In particular, having more example scripts would be a huge help. If you have
a program that uses python-twitter and would like a link in the documentation,
submit a pull request against ``twitter/doc/getting_started.rst`` and add your
program at the bottom.

The twitter.Status and ``twitter.User`` classes are going to be hard to keep in sync with the API if the API changes. More of the code could probably be written with introspection.

The ``twitter.Status`` and ``twitter.User`` classes could perform more validation on the property setters.

----------------
More Information
----------------

Please visit `the google group <http://groups.google.com/group/python-twitter>`_ for more discussion.

------------
Contributors
------------

Originally two libraries by DeWitt Clinton and Mike Taylor which was then merged into python-twitter.

Now it's a full-on open source project with many contributors over time. See AUTHORS.rst for the complete list.

-------
License
-------

| Copyright 2007-2016 The Python-Twitter Developers
|
| Licensed under the Apache License, Version 2.0 (the 'License');
| you may not use this file except in compliance with the License.
| You may obtain a copy of the License at
|
|     http://www.apache.org/licenses/LICENSE-2.0
|
| Unless required by applicable law or agreed to in writing, software
| distributed under the License is distributed on an 'AS IS' BASIS,
| WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
| See the License for the specific language governing permissions and
| limitations under the License.


Originally two libraries by DeWitt Clinton and Mike Taylor which was then merged into python-twitter.

Now it's a full-on open source project with many contributors over time:

* Jodok Batlogg,
* Kyle Bock,
* Brad Choate,
* Robert Clarke,
* Jim Cortez,
* Pierre-Jean Coudert,
* Aish Raj Dahal,
* Thomas Dyson,
* Jim Easterbrook
* Yoshinori Fukushima,
* Hameedullah Khan,
* Osama Khalid,
* Omar Kilani,
* Domen Kožar,
* Robert Laquey,
* Jason Lemoine,
* Pradeep Nayak,
* Ian Ozsvald,
* Nicolas Perriault,
* Trevor Prater,
* Glen Tregoning,
* Lars Weiler,
* Sebastian Wiesinger,
* Jake Robinson,
* Muthu Annamalai,
* abloch,
* cahlan,
* dpslwk,
* edleaf,
* ecesena,
* git-matrix,
* sbywater,
* thefinn93,
* themylogin,


2016-05-25
  Going forward all changes will be tracked in docs/changelog.rst

2015-12-28
  Large number of changes related to making the code Python v3 compatible.
  See the messy details at https://github.com/bear/python-twitter/pull/251

  Pull Requests
      #525 Adds support for 280 character limit for tweets by trevorprater
      #267 initialize Api.__auth fixes #119 by rbpasker
      #266 Add full_text and page options in GetDirectMessages function by mistersalmon
      #264 Updates Media object with new methods, adds id param, adds tests by jeremylow
      #262 Update get_access_token.py by lababidi
      #261 Adding Collections by ryankicks
      #260 Added UpdateBackgroundImage method and added profile_link_color argument to UpdateProfile by BrandonBielicki
      #259 Added GetFriendIDsPaged by RockHoward
      #254 Adding api methods for suggestions and suggestions/:slug by trentstollery
      #253 Added who parameter to api.GetSearch by wilsonand1
      #250 adds UpdateFriendship (shared Add/Edit friendship) by jheld
      #249 Fixed Non-ASCII printable representation in Trend by der-Daniel
      #246 Add __repr__ for status by era
      #245 Python-3 Fix: decode bytestreams for json load by ligthyear
      #243 Remove references to outdated API functionality: GetUserByEmail by Vector919
      #239 Correct GetListsList docstring by tedmiston

  Probably a whole lot that I missed - ugh!

2017-11-11
  Added support for 280 character limit

2015-10-05
  Added who to api.GetSearch

2014-12-29
  removed reference to simplejson

2014-12-24
  bump version to v2.3
  bump version to v2.2
  PEP8 standardization

2014-07-10
  bump version to v2.1

2014-07-10
  update copyright years
  change setup.py to allow installing via wheel
  renamed README.md to README.rst
  added AUTHORS.rst

2014-02-17
  changed version to 1.3 and then to 1.3.1 because I forgot to include CHANGES
  fix Issue 143 - GetStatusOembed() url parameter was being stomped on
  fix debugHTTP in a brute force way but it works again
  Add id_str to Status class
  Added LookupFriendship() method for checking follow status
    pull request from lucas
  Fix bug of GetListMembers when specifying `owner_screen_name`
    pull request from shichao-an

2014-01-18
  backfilling varioius lists endpoints
  added a basic user stream call

2014-01-17
  changed to version 1.2
  fixed python 3 issue in setup.py (print statements)
  fixed error in CreateList(), changed count default for GetFollowers to 200 and added a GetFollowersPaged() method

need to backfill commit log entries!

2013-10-06
  changed version to 1.1
  The following changes have been made since the 1.0.1 release

  Remove from ParseTweet the Python 2.7 only dict comprehension item
  Fix GetListTimeline condition to enable owner_screen_name based fetching
  Many fixes for readability and PEP8
  Cleaning up some of the package importing. Only importing the functions that are needed
  Also added first build of the sphinx documentation. Copied some info from the readme to the index page
  Added lines to setup.py to help the user troubleshoot install problems. #109
  Removed the OAuth2 lines from the readme
  Removed OAuth2 library requirements
  Added GetListMembers()


2013-06-07
  changed version to 1.0.1
  added README bit about Python version requirement

2013-06-04
  changed version to 1.0
  removed doc directory until we can update docs for v1.1 API
  added to package MANIFEST.in the testdata directory

2013-05-28
  bumped version to 1.0rc1
  merged in api_v1.1 branch

  The library is now only for Twitter API v1.1

2013-03-03
  bumped version to 0.8.7

  removed GetPublicTimeline from the docs so as to stop confusing
  new folks since it was the first example given ... d'oh!

2013-02-10
  bumped version to 0.8.6

  update requirements.txt to remove distribute reference
  github commit 3b9214a879e5fbd03036a7d4ae86babc03784846

  Merge pull request #33 from iElectric/profile_image_url_https
  github commit 67cbb8390701c945a48094795474ca485f092049
  patch by iElectric on github

  Change User.NewFromJsonDict so that it will pull from either
  profile_image_url_https or profile_image_url to keep older code
  working properly if they have stored older json data

2013-02-07
  bumped version to 0.8.5
  lots of changes have been happening on Github and i've been
  very remiss in documenting them here in the Changes file :(

  this version is the last v1.0 API release and it's being made
  to push to PyPI and other places

  all work now will be on getting the v1.1 API supported

2012-11-04
  https://github.com/bear/python-twitter/issues/4
  Api.UserLookUp() throws attribute error when corresponding screen_name is not found

  https://github.com/bear/python-twitter/pull/5
  Merge pull request #5 from thefinn93/master
  Setup.py crashes because the README file is now named README.md

  Update .gitignore to add the PyCharm data directory

2012-10-16
 http://code.google.com/p/python-twitter/issues/detail?id=233
 Patch by dan@dans.im
 Add exclude_replies parameter to GetUserTimeline

 https://github.com/bear/python-twitter/issues/1
 Bug reported by michaelmior on github
 get_access_token.py attempts Web auth

2011-12-03
 https://code.google.com/p/python-twitter/source/detail?r=263fe2a0db8be23347e92b81d6ab3c33b4ef292f
 Comment by qfuxiang to the above changeset
 The base url was wrong for the Followers API calls

 https://code.google.com/p/python-twitter/issues/detail?id=213
 Add include_entities parameter to GetStatus()
 Patch by gaelenh

 https://code.google.com/p/python-twitter/issues/detail?id=214
 Change PostUpdate() so that it takes the shortened link into
 account.  Small tweak to the patch provided to make the
 shortened-link length set by a API value instead of a constant.
 Patch by ceesjan.ytec

 https://code.google.com/p/python-twitter/issues/detail?id=216
 AttributeError handles the fact that win* doesn't implement
 os.getlogin()
 Patch by yaleman

 https://code.google.com/p/python-twitter/issues/detail?id=217
 As described at https://dev.twitter.com/docs/api/1/get/trends,
 GET trends (corresponding to Api.GetTrendsCurrent) is now
 deprecated in favor of GET trends/:woeid. GET trends also now
 requires authentication, while trends/:woeid doesn't.
 Patch and excellent description by jessica.mckellar

 https://code.google.com/p/python-twitter/issues/detail?id=218
 Currently, two Trends containing the same information
 (name, query, and timestamp) aren't considered equal because
 __eq__ isn't overridden, like it is for Status, User, and the
 other Twitter objects.
 Patch and excellent description by jessica.mckellar

 https://code.google.com/p/python-twitter/issues/detail?id=220
 https://code.google.com/p/python-twitter/issues/detail?id=211
 https://code.google.com/p/python-twitter/issues/detail?id=206
 All variations on a theme - basically Twitter is returning
 something different for an error payload.  Changed code to
 check for both 'error' and 'errors'.

2011-05-08

 https://code.google.com/p/python-twitter/issues/detail?id=184
 A comment in this issue made me realize that the parameter sanity
 check for max_id was missing in GetMentions() - added

 First pass at working in some of the cursor support that has been
 in the Twitter API but we haven't made full use of - still working
 out the small issues.

2011-04-16

 bumped version to 0.8.3
 released 0.8.2 to PyPI
 bumped version to 0.8.2

 Issue 193
 http://code.google.com/p/python-twitter/issues/detail?id=193
 Missing retweet_count field on Status object
 Patch (with minor tweaks) by from alissonp

 Issue 181
 http://code.google.com/p/python-twitter/issues/detail?id=181
 Add oauth2 to install_requires parameter list and also updated
 README to note that the oauth2 lib can be found in two locations

 Issue 182, Issue 137, Issue 93, Issue 190
 language value missing from User object
 Added 'lang' item and also some others that were needed:
   verified, notifications, contributors_enabled and listed_count
 patches by wreinerat, apetresc, jpwigan and ghills

2011-02-26

 Issue 166
 http://code.google.com/p/python-twitter/issues/detail?id=166
 Added a basic, but sadly needed, check when parsing the json
 returned by Twitter as Twitter has a habit of returning the
 failwhale HTML page for a json api call :(
 Patch (with minor tweaks) by adam.aviv

 Issue 187
 http://code.google.com/p/python-twitter/issues/detail?id=187
 Applied patch by edward.hades to fix issue where MaximumHitFrequency
 returns 0 when requests are maxed out

 Issue 184
 http://code.google.com/p/python-twitter/issues/detail?id=184
 Applied patch by jmstaley to put into the GetUserTimeline API
 parameter list the max_id value (it was being completely ignored)

2011-02-20

 Added retweeted to Status class
 Fixed Status class to return Hashtags list in AsDict() call

 Issue 185
 http://code.google.com/p/python-twitter/issues/detail?id=185
 Added retweeted_status to Status class - patch by edward.hades

 Issue 183
 http://code.google.com/p/python-twitter/issues/detail?id=183
 Removed errant print statement - reported by ProgVal

2010-12-21

 Setting version to 0.8.1

 Issue 179
 http://code.google.com/p/python-twitter/issues/detail?id=179
 Added MANIFEST.in to give setup.py sdist some clues as to what
 files to include in the tarball

2010-11-14

 Setting version to 0.8 for a bit as having a branch for this is
 really overkill, i'll just take DeWitt advice and tag it when
 the release is out the door

 Issue 175
 http://code.google.com/p/python-twitter/issues/detail?id=175
 Added geo_enabled to User class - basic parts of patch provided
 by adam.aviv with other bits added by me to allow it to pass tests

 Issue 174
 http://code.google.com/p/python-twitter/issues/detail?id=174
 Added parts of adam.aviv's patch - the bits that add new field items
 to the Status class.

 Issue 159
 http://code.google.com/p/python-twitter/issues/detail?id=159
 Added patch form adam.aviv to make the term parameter for GetSearch()
 optional if geocode parameter is supplied

2010-11-03

 Ran pydoc to generate docs

2010-10-16

 Fixed bad date in previous CHANGES entry

 Fixed source of the python-oauth2 library we use: from brosner
 to simplegeo

 I made a pass thru the docstrings and updated many to be the
 text from the current Twitter API docs.  Also fixed numerous
 whitespace issues and did a s/[optional]/[Optional]/ change.

 Imported work by Colin Howe that he did to get the tests working.
 http://code.google.com/r/colinthehowe-python-twitter-tests/source/detail?r=6cff589aca9c955df8354fe4d8e302ec4a2eb31c
 http://code.google.com/r/colinthehowe-python-twitter-tests/source/detail?r=cab8e32d7a9c34c66d2e75eebc7a1ba6e1eac8ce
 http://code.google.com/r/colinthehowe-python-twitter-tests/source/detail?r=b434d9e5dd7b989ae24483477e3f00b1ad362cc5

 Issue 169
 http://code.google.com/p/python-twitter/issues/detail?id=169
 Patch by yaemog which adds missing Trends support.

 Issue 168
 http://code.google.com/p/python-twitter/issues/detail?id=168
 Only cache successful results as suggested by yaemog.

 Issue 111
 http://code.google.com/p/python-twitter/issues/detail?id=111
 Added a new GetUserRetweets() call as suggested by yash888
 Patch given was adjusted to reflect the current code requirements.

 Issue 110
 Added a VerifyCredentials() sample call to the README example

 Issue 105
 Added support for the page parameter to GetFriendsTimeline()
 as requested by jauderho.
 I also updated GetFriendsTimeline() to follow the current
 Twitter API documentation

 Somewhere in the patch frenzy of today an extra GetStatus()
 def was introduced!?! Luckily it was caught by the tests.
 wooo tests! \m/

 Setting version to 0.8

 r0.8 branch created and trunk set to version 0.9-devel

2010-09-26

 Issue 150
 http://code.google.com/p/python-twitter/issues/detail?id=150
 Patch by blhobbes which removes a double quoting issue that
 was happening for GetSearch()
 Reported by huubhuubbarbatruuk

 Issue 160
 http://code.google.com/p/python-twitter/issues/detail?id=160
 Patch by yaemog which adds support for include_rts and
 include_entities support to GetUserTimeline and GetPublicTimeline
 Small tweaks post-patch

 Applied docstring tweak suggested by dclinton in revision comment
 http://code.google.com/p/python-twitter/source/detail?r=a858412e38f7e3856fef924291ef039284d3a6e1
 Thanks for the catch!

 Issue 164
 http://code.google.com/p/python-twitter/issues/detail?id=164
 Patch by yaemog which adds GetRetweets support.
 Small tweaks and two typo fixes post-patch.

 Issue 165
 http://code.google.com/p/python-twitter/issues/detail?id=165
 Patch by yaemog which adds GetStatus support.
 Small tweaks post-patch

 Issue 163
 http://code.google.com/p/python-twitter/issues/detail?id=163
 Patch by yaemog which adds users/lookup support.
 Small tweaks to docstring only post-patch.

 Changed username/password parameter to Api class to be
 consumer_key/consumer_secret to better match the new
 oAuth only world that Twitter has demanded.

 Added debugHTTP to the parameter list to Api class to
 control if/when the urllib debug output is displayed.

2010-08-25

 First pass at adding list support.
 Added a new List class and also added to the Api class
 new methods for working with lists:

   CreateList(self, user, name, mode=None, description=None)
   DestroyList(self, user, id)
   CreateSubscription(self, owner, list)
   DestroySubscription(self, owner, list)
   GetSubscriptions(self, user, cursor=-1)
   GetLists(self, user, cursor=-1)

2010-08-24

 Fixed introduced bug in the Destroy* and Create* API calls
 where any of the routines were passing in an empty dict for
 POST data.  Before the oAuth change that was enough to tell
 _FetchUrl() to use POST instead of GET but now a non-empty
 dict is required.

 Issue 144
 http://code.google.com/p/python-twitter/issues/detail?id=144
 GetFriends() where it was failing with a 'unicode object has
 no attribute get'. This was caused when Twitter changed how
 they return the JSON data. It used to be a straight list but
 now there are some elements *and* then the list.

2010-08-18

 Applied the json/simplejson part of the patch found
 in Issue 64 (http://code.google.com/p/python-twitter/issues/detail?id=64)
 Patch provided by Thomas Bohmbach

 Applied patch provided by liris.pp in Issue 147
 http://code.google.com/p/python-twitter/issues/detail?id=147
 Ensures that during a PostStatus we count the length using a unicode aware
 len() routine.  Tweaked patch slightly to take into account that the
 twitter.Api() instance may have been setup with None for input_encoding.

2010-08-17

 Fixed error in the POST path for _FetchUrl() where by
 I show to the world that yes, I do make last minute
 changes and completely forget to test them :(
 Thanks to Peter Sanchez for finding and pointing to
 working code that showed the fix

2010-08-15

 Added more help text (I hope it helps) to the README
 and also to get_access_token.py.

 Added doctext notes to twitter.Api() parameter list
 to explain more about oAuth.

 Added import exception handling for parse_qs() and
 parse_qsl() as it seems those funcitons moved between
 2.5 and 2.6 so the oAuth update broke the lib under
 python2.5.  Thanks to Rich for the bug find (sorry
 it had to be found the hard way!)

 from changeset 184:60315000989c by DeWitt
 Update the generated twitter.py docs to match the trunk

2010-08-14

 Fixed silly typo in _FetchUrl() when doing a POST
 Thanks to Peter Sanchez for the find and fix!

 Added some really basic text to the get_access_token.py
 startup output that explains why, for now, you need to
 visit Twitter and get an Application key/secret to use
 this library

2010-08-12

 Updated code to use python-oauth2 library for authentication.
 Twitter has set a deadline, 2010-08-16 as of this change, for
 the switch from Basic to oAuth.

 The oAuth integration was inspired by the work done by
 Hameedullah Khan and others.

 The change to using python-oauth2 library was done purely to
 align python-twitter with an oauth library that was maintained
 and had tests to try and minimize grief moving forward.

 Slipped into GetFriendsTimeline() a new parameter, retweets, to
 allow the call to pull from the "friends_timeline" or the
 "home_timeline".

 Fixed some typos and white-space issues and also updated the
 README to point to the new Twitter Dev site.

2010-08-02

 Updated copyright information.

2010-06-13

 Applied changeset from nicdumz repo nicdumz-cleaner-python-twitter
   r=07df3feee06c8d0f9961596e5fceae9e74493d25
   datetime is required for MaximumHitFrequency

 Applied changeset from nicdumz repo nicdumz-cleaner-python-twitter
   r=dd669dff32d101856ed6e50fe8bd938640b04d77
   update source URLs in README

 Applied changeset from nicdumz repo nicdumz-cleaner-python-twitter
   r=8f0796d7fdcea17f4162aeb22d3c36cb603088c7
   adjust tests to reflect http://twitter.com -> https://twitter.com change

 Applied changeset from nicdumz repo nicdumz-cleaner-python-twitter
   r=3c05b8ebe59eca226d9eaef2760cecca9d50944a
   tests: add .info() method to objects returned by our Mockup handler
   This is required to completely mimick urllib, and have successful
   response.headers attribute accesses.

 Applied partial patch for Issue 113
 http://code.google.com/p/python-twitter/issues/detail?id=113

   The partial bit means we changed the parameter from "page" to "cursor"
   so the call would work.  What was left out was a more direct way
   to return the cursor value *after* the call and also in the patch
   they also changed the method to return an iterator.

2010-05-17

 Issue 50 http://code.google.com/p/python-twitter/issues/detail?id=50
 Applied patch by wheaties.box that implements a new method to return
 the Rate Limit Status and also adds the new method MaximumHitFrequency

 Multiple typo, indent and whitespace tweaks

 Issue 60 http://code.google.com/p/python-twitter/issues/detail?id=60
 Pulled out new GetFavorites and GetMentions methods from the patch
 submitted by joegermuska

 Issue 62 http://code.google.com/p/python-twitter/issues/detail?id=62
 Applied patch from lukev123 that adds gzip compression to the GET
 requests sent to Twitter. The patch was modified to default gzip to
 False and to allow the twitter.API class instantiation to set the
 value to True.  This was done to not change current default
 behaviour radically.

 Issue 80 http://code.google.com/p/python-twitter/issues/detail?id=80
 Fixed PostUpdate() call example in the README

2010-05-16

 Issue 19 http://code.google.com/p/python-twitter/issues/detail?id=19
 TinyURL example and the idea for this comes from a bug filed by
 acolorado with patch provided by ghills.

 Issue 37 http://code.google.com/p/python-twitter/issues/detail?id=37
 Added base_url to the twitter.API class init call to allow the user
 to override the default https://twitter.com base.  Since Twitter now
 supports https for all calls I (bear) changed the patch to default to
 https instead of http.
 Original issue by kotecha.ravi, patch by wiennat and with implementation
 tweaks by bear.

 Issue 45 http://code.google.com/p/python-twitter/issues/detail?id=45
 Two grammar fixes for relative_created_at property
 Patches by thomasdyson and chris.boardman07

2010-01-24

 Applying patch submitted to fix Issue 70
 http://code.google.com/p/python-twitter/issues/detail?id=70

 The patch was originally submitted by user ghills, adapted by livibetter and
 adapted even further by JimMoefoe (read the comments for the full details :) )

 Applying patch submitted by markus.magnuson to add new method GetFriendIDs
 Issue 94 http://code.google.com/p/python-twitter/issues/detail?id=94

2009-06-13

 Releasing 0.6 to help people avoid the Twitpocalypse.

2009-05-03

 Support hashlib in addition to the older md5 library.

2009-03-11

 Added page parameter to GetReplies, GetFriends, GetFollowers, and GetDirectMessages

2009-03-03

  Added count parameter to GetFriendsTimeline

2009-03-01
  Add PostUpdates, which automatically splits long text into multiple updates.

2009-02-25

  Add in_reply_to_status_id to api.PostUpdate

2009-02-21

  Wrap any error responses in a TwitterError
  Add since_id to GetFriendsTimeline and GetUserTimeline

2009-02-20

  Added since and since_id to Api.GetReplies

2008-07-10

  Added new properties to User and Status classes.
  Removed spurious self-import of the twitter module
  Added a NOTICE file
  Require simplejson 2.x or later
  Added get/create/destroy favorite flags for status messages.
  Bug fix for non-tty devices.

2007-09-13

  Unset the executable bit on README.

2007-09-13

  Released version 0.5.
  Added back support for setuptools (conditionally)
  Added support for X-Twitter-* HTTP headers
  Fixed the tests to work across all timezones
  Removed the 140 character limit from PostUpdate
  Added support for per-user tmp cache directories

2007-06-13

  Released 0.4.
  Fixed a unicode error that prevented tweet.py from working.
  Added DestroyStatus
  Added DestroyDirectMessage
  Added CreateFriendship
  Added DestoryFriendship

2007-06-03

  Fixed the bug that prevented unicode strings being posted
  Username and password now set on twitter.Api, not individual method calls
  Added SetCredentials and ClearCredentials
  Added GetUser ("users/show" in the twitter web api)
  Added GetFeatured
  Added GetDirectMessages
  Added GetStatus ("statuses/show" in the twitter web api)
  Added GetReplies
  Added optional since_id parameter on GetPublicTimeline
  Added optional since parameter on GetUserTimeline
  Added optional since and user parameters on GetFriendsTimeline
  Added optional user parameter on GetFriends

2007-04-27

  Modified examples/twitter-to-xhtml.py to handle unicode
  Dropped dependency on setuptools (too complicated/buggy)
  Added unicode test cases
  Fixed issue 2 "Rename needs an unlink in front"

2007-04-02

  Released 0.3.
  Use gmtime not localtime to calculate relative_created_at.

2007-03-26

  Released 0.2
  GetUserTimeline can accept userid or username.

2007-03-21

  Calculate relative_created_at on the fly

2007-01-28

  Released 0.1
  Initial checkin of python-twitter



