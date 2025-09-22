wazo-confgend
=============
[![Build Status](https://jenkins.wazo.community/buildStatus/icon?job=wazo-confgend)](https://jenkins.wazo.community/job/wazo-confgend)

wazo-confgend is a service for generating configuration files.


Running unit tests
------------------

```
apt-get install libpq-dev python3-dev libffi-dev libyaml-dev
pip install tox
tox --recreate -e py311
```
