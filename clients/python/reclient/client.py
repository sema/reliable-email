
import urllib
import urllib2


class ReClient(object):

    def __init__(self, server_url):
        """
        :param server_url: url to a reliable-email web frontend
        :return:
        """
        self._url = server_url

    def submit(self, subject, body, to_email, to_name='', from_email='', from_name=''):
        """
        Submit an email to the reliable-email service.

        :param str subject:
        :param str body:
        :param str to_email:
        :param str to_name: (optional)
        :param str from_email: (optional)
        :param str from_name: (optional)
        :return: True if submitted, otherwise it returns False
        """

        data = urllib.urlencode({
            'subject': subject,
            'body': body,
            'to': to_email,
            'to_name': to_name,
            'from': from_email,
            'from_name': from_name
        })

        try:
            request = urllib2.Request(self._url, data)
            response = urllib2.urlopen(request)
        except urllib2.URLError:
            return False

        return response.getcode() == 200