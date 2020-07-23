from flask import Flask, render_template_string
import requests

class Mailer:
    def __init__(self, api_key, api_domain, api_url='https://api.mailgun.net/v3/', verbose=True):
        self.api_key = api_key
        self.api_url = api_url
        self.domain = api_domain
        self.base_url = self.api_url + self.domain
        self.verbose = verbose
    
    def _log(self, *args, **kwargs):
        if self.verbose:
            print('[Mailer]', *args, **kwargs)

    def send_message(self, recepient, name, username, subject, body, **kwargs):
        with Flask('email_render').app_context(): # render_template_string needs app context, ugh
            email_data = {
                'from': '%s <%s@%s>' % (name, username, self.domain),
                'to': [ recepient ] if type(recepient) == str else recepient,
                'subject': render_template_string(subject, **kwargs),
                'html': render_template_string(body, **kwargs) }
        self._log('Email sent to %s, subject: \'%s`\'' % (email_data['to'], email_data['subject']))
        return requests.post(self.base_url + '/messages', auth=('api', self.api_key), data=email_data)