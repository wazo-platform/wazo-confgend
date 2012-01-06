#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Guillaume Bour <gbour@proformatique.com>"
__license__ = """
    Copyright (C) 2010-2011  Avencall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""
import httplib, urllib, base64, socket
import cjson as json

class JSONClient(object):
    objects = {
 		# object name     : [url part1                 , url part2         , allowed methods, real name (None is same as key)]

            # general settings
        'sip'             : ['service/ipbx'            , 'general_settings', None, ('view')],
        'iax'             : ['service/ipbx'            , 'general_settings', None, ('view')],
        'voicemail'       : ['service/ipbx'            , 'general_settings', None, ('view')],
        'phonebook'       : ['service/ipbx'            , 'general_settings', None, ('view')],
        'advanced'        : ['service/ipbx'            , 'general_settings', None, ('view')],


      'entity'          : ['xivo/configuration'      , 'manage'],
      'users'           : ['service/ipbx'            , 'pbx_settings'    , None, ('list', 'view')],
      'incall'          : ['service/ipbx'            , 'call_management'],

      'queueskill'      : ['service/ipbx'            , 'call_center'],
      'queueskillrules' : ['service/ipbx'            , 'call_center'],
      'agents'          : ['service/ipbx'            , 'call_center'],

      'mail'            : ['xivo/configuration'      , 'network'],
      'dhcp'            : ['xivo/configuration'      , 'network'],
      'monitoring'      : ['xivo/configuration'      , 'support'],

        'siptrunks'       : ['service/ipbx'            , 'trunk_management', 'sip', ('list', 'view')],
        'iaxtrunks'       : ['service/ipbx'            , 'trunk_management', 'iax', ('list', 'view')],
    }

    def __init__(self, ip='localhost', port=80, ssl=False, username=None, password=None):
        self.headers = {
            "Content-type": "application/json",
            "Accept": "text/plain"
        }

        if username is not None:
            self.headers['Authorization'] = 'Basic ' + \
                base64.encodestring('%s:%s' % (username, password))[:-1]
        self.baseuri = '/%s/json.php/restricted/%s/%s/?act=%s'

        if ssl:
            self.conn = httplib.HTTPSConnection(ip, port)
        else:
            self.conn = httplib.HTTPConnection(ip, port)


    def request(self, method, uri, params=None):
        if method == 'POST':
            params = json.encode(params)
        elif params:
            mark = '&' if '?' in uri else '?'
            uri = "%s%s%s" % (uri, mark, urllib.urlencode(params))
            params = None

        print 'request= ', uri
        try:
          self.conn.request(method, uri, params, self.headers)
          response = self.conn.getresponse()
          data = response.read()
        except socket.error, e:
          return (None, e)

        return (response, data)

    def __check(self, obj, fnc):
        if obj not in self.objects:
            raise Exception('Unknown %s object' % obj)

        params = self.objects[obj]
        if fnc not in params[3]:
            raise Exception('%s action not allowed on %s object' (fnc, obj))

        obj = params[2] if params[2] is not None else obj
        return obj, params


    def list(self, obj):
        obj, params = self.__check(obj, 'list')

        return self.request('GET',
            self.baseuri % (params[0], params[1], obj, 'list')
        )

    def add(self, obj, content):
        obj, params = self.__check(obj, 'add')

        return self.request('POST',
            self.baseuri % (params[0], params[1], obj, 'add'),
            content
        )

    def edit(self, obj, content):
        obj, params = self.__check(obj, 'edit')

        return self.request('POST',
            self.baseuri % (params[0], params[1], obj, 'edit'),
            content
        )

    def view(self, obj, id=None):
        """
            NOTE: id is not set for general objects (sip, iax, ...)
                elsewhere it must be set
        """
        obj, params = self.__check(obj, 'view')

        return self.request('GET',
            self.baseuri % (params[0], params[1], obj, 'view'),
            {'id': id}
        )

    def delete(self, obj, id):
        obj, params = self.__check(obj, 'view')

        return self.request('GET',
            self.baseuri % (params[0], params[1], obj, 'delete'),
            {'id': id}
        )



