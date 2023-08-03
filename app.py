# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
from __future__ import print_function

import os
import sys
import wsgiref.simple_server
import gspread
from argparse import ArgumentParser
from dotenv import load_dotenv

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
          
          # The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1G9DcmPvvDmOvrYvPaK261FdNZgdnBIgAuhE0W3eH4DA'
SAMPLE_RANGE_NAME = 'Reports!A2:B99'

load_dotenv()

from builtins import bytes
from linebot.v3 import (
    WebhookParser
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.utils import PY3

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

parser = WebhookParser(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)

def application(environ, start_response):
    gc = gspread.oauth(
        credentials_filename='credentials.json',
        authorized_user_filename='token.json'
    )

    spreadsheet = gc.open_by_key(SAMPLE_SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet("Reports")

    # google sheet API stuff
    # creds = None

    # if os.path.exists('token.json'):
    #     creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'credentials.json', SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open('token.json', 'w') as token:
    #         token.write(creds.to_json())

    # check request path
    if environ['PATH_INFO'] != '/callback':
        start_response('404 Not Found', [])
        return create_body('Not Found')

    # check request method
    if environ['REQUEST_METHOD'] != 'POST':
        start_response('405 Method Not Allowed', [])
        return create_body('Method Not Allowed')

    # get X-Line-Signature header value
    signature = environ['HTTP_X_LINE_SIGNATURE']

    # get request body as text
    wsgi_input = environ['wsgi.input']
    content_length = int(environ['CONTENT_LENGTH'])
    body = wsgi_input.read(content_length).decode('utf-8')

    # parse webhook body
    try:
        events = parser.parse(body, signature)

    except InvalidSignatureError:
        start_response('400 Bad Request', [])
        return create_body('Bad Request')
    

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue
        
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

        print(event.message.text)
        if(event.message.text == "/report"):
            try: 
                reportRow=worksheet.row_values(2)
                
                reportStatus=worksheet.cell(2,4).value

                if(len(reportRow) == 0):
                    msg="No report exists!"

                elif reportStatus is not None:
                    msg="All reports have been reported!"

                else:
                    reporter=worksheet.cell(2, 3).value
                    latestDate=worksheet.cell(2, 1).value
                    latestReport=worksheet.cell(2, 2).value
                    msg="["+latestDate+"] "+reporter+": \""+latestReport+"\""

                    worksheet.update('D2', "Reported!")

                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=msg)]
                    )
                )
            except Exception as e:
                print(e.with_traceback)
                start_response('400 Bad Request', [])
                return create_body('Bad Request')

        # else:
        #     with ApiClient(configuration) as api_client:
        #         line_bot_api = MessagingApi(api_client)
        #         line_bot_api.reply_message_with_http_info(
        #             ReplyMessageRequest(
        #                 reply_token=event.reply_token,
        #                 messages=[TextMessage(text=event.message.text)]
        #             )
        #         )

    start_response('200 OK', [])
    return create_body('OK')


def create_body(text):
    if PY3:
        return [bytes(text, 'utf-8')]
    else:
        return text


if __name__ == '__main__':
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    options = arg_parser.parse_args()

    httpd = wsgiref.simple_server.make_server('', options.port, application)
    httpd.serve_forever()
