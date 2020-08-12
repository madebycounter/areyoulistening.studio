from flask import Flask, render_template_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class Mailer:
    def __init__(self, api_key, verbose=True):
        self.api_key = api_key
        self.verbose = verbose
        self.sendgrid = SendGridAPIClient(self.api_key)
    
    def _log(self, *args, **kwargs):
        if self.verbose:
            print('[Mailer]', *args, **kwargs)

    def send_message(self, recepient, name, username, subject, body, reply_to=None, **kwargs):
        with Flask('email_render').app_context(): # render_template_string needs app context, ugh
            email_data = {
                'from_email': '%s <%s>' % (name, username),
                'to_emails': [ recepient ] if type(recepient) == str else recepient,
                'subject': render_template_string(subject, **kwargs),
                'html_content': render_template_string(body, **kwargs) }
        message = Mail(**email_data)
        message.reply_to = reply_to if reply_to else '%s <%s>' % (name, username)
        response = self.sendgrid.send(message)
        self._log('Email sent to %s, subject: \'%s`\'' % (email_data['to_emails'], email_data['subject']))

        return response