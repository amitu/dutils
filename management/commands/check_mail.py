#!/usr/bin/env python
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import poplib, rfc822
from email import parser

from optparse import make_option

from dutils.signals import new_pop3_mail

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--host', "-H", dest='host', 
            default=getattr(settings, "POP3_HOST", ""),
            help='POP3 host, default=%s' % getattr(settings, "POP3_HOST", "")
        ),
        make_option(
            '--port', "-P", dest='port', type="int",
            default=getattr(settings, "POP3_PORT", 110),
            help='POP3 port, default=%s' % getattr(settings, "POP3_PORT", 110)
        ),
        make_option(
            '--user', "-u", dest='user', 
            default=getattr(settings, "POP3_USER", ""),
            help='POP3 username, default=%s' % getattr(
                settings, "POP3_USER", ""
            )
        ),
        make_option(
            '--password', "-p", dest='password', 
            default=getattr(settings, "POP3_PASSWORD", ""),
            help='Password, default=%s' % getattr(
                settings, "POP3_PASSWORD", ""
            )
        ),
        make_option(
            '--ssl', "-s", dest='ssl', action="store_true",
            default=getattr(settings, "POP3_SECURE", False),
            help='Use SSL?, default=%s' % getattr(
                settings, "POP3_USE_SSL", False
            )
        ),
        make_option(
            '--leave', "-l", dest='leave', action="store_true",
            default=getattr(settings, "POP3_LEAVE", False),
            help='Leave mails on server?, default=%s' % getattr(
                settings, "POP3_LEAVE", False
            )
        ),
        make_option(
            '--delete', "-d", dest='leave', action="store_false",
            default=not getattr(settings, "POP3_LEAVE", False),
            help='Delete mails from server?, default=%s' % (
                not getattr(settings, "POP3_LEAVE", False)
            )
        ),
        make_option(
            '--number', "-n", dest='number', type="int",
            default=getattr(settings, "POP3_NUMBER_OF_MAILS", 5),
            help='Number of mails to download, default=%s' % getattr(
                settings, "POP3_NUMBER_OF_MAILS", 5
            )
        ),
    )
    help = 'Get mails from POP3 server. Sends signals. Supports SSL.'

    def handle(self, *args, **options):
        print options
        if options["ssl"]:
            pop3 = poplib.POP3_SSL(options["host"], options["port"])
        else:
            pop3 = poplib.POP3(options["host"], options["port"])
        print pop3.getwelcome()
        print pop3.user(options["user"])
        print pop3.pass_(options["password"])
        for i_uid in pop3.uidl()[1][:options["number"]+1]:
            i, uid = i_uid.split()
            message = pop3.retr(i)
            message = "\n".join(message[1])
            message = parser.Parser().parsestr(message)
            message.id = uid
            message.subject = message["subject"]
            message.sender = rfc822.parseaddr(message["from"])[1]
            print uid, message["subject"], message["from"], message["date"]
            if not options["leave"]: pop3.dele(i)
            new_pop3_mail.send(sender=pop3, uid=uid, mail=message)

