#!/usr/bin/env python3
#
# Requirements:
#    pony
#    PyMySQL
#    jinja2
#


from pony import orm
from pony.orm import unicode
from datetime import datetime
from base64 import b64decode
from jinja2 import Environment, FileSystemLoader
import os
from config import debug, tmpl_dir, rc_path, database
import subprocess
import logging
import sys


FORMAT = "%(asctime)-15s %(user)-8s %(message)s"
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('getmail_postfix')

if debug:
    logger.setLevel(logging.DEBUG)


class Fetchmail(database.Entity):
    """
    Pony ORM model of the Fetchmail table
    """
    domain = orm.Required(unicode)
    mailbox = orm.Required(unicode)
    src_server = orm.Required(unicode)
    src_user = orm.Required(unicode)
    src_password = orm.Required(unicode)
    usessl = orm.Optional(bool)
    fetchall = orm.Optional(bool)
    keep = orm.Optional(bool)
    modified = orm.Required(datetime)
    active = orm.Required(bool)


def get_getmailrc(mailbox_user, mailbox):
    j2_env = Environment(loader=FileSystemLoader(tmpl_dir),
                         trim_blocks=True)

    return j2_env.get_template('getmailrc.tmpl').render(
        box=box,
        context={
            'multi': False,
            'base_path': base_path,
            'mailbox_user': mailbox_user,
            'src_password': b64decode(mailbox.src_password).decode('utf-8'),
            'rc_path': rc_path.rstrip('/')
        }
    )


def is_running():
    proc = subprocess.Popen(
        'ps ax | grep /usr/bin/getmail | grep -c --invert-match grep',
        shell=True,
        stdout=subprocess.PIPE
    )
    count = proc.stdout.readline()
    return count.decode('utf-8').strip() != '0'


if __name__ == "__main__":
    if debug:
        # turn on debug mode
        orm.sql_debug(True)

    if not os.path.isdir(rc_path):
        os.mkdir(rc_path)

    if is_running():
        logger.debug("Getmail is running, exiting now", extra={'user': '-'})
        sys.exit()

    # use db_session as a context manager
    with orm.db_session:
        # map the models to the database
        database.generate_mapping(create_tables=False)

        mailboxes = orm.select(mailbox for mailbox in Fetchmail if mailbox.active)
        for box in mailboxes:
            mailbox_user = box.mailbox.split('@')[0]

            context = {
                'user': mailbox_user
            }

            rc_file_name = 'getmailrc.{mailbox_user}{box.id}'.format(mailbox_user=mailbox_user, box=box)
            rc_file = os.path.join(rc_path, rc_file_name)

            if not os.path.isfile(rc_file) or datetime.fromtimestamp(os.path.getmtime(rc_file)) < box.modified:
                with open(rc_file, 'w') as new_getmailrc:
                    logger.debug('Creating new rc file for %s ...', mailbox_user, extra=context)
                    new_getmailrc.write(get_getmailrc(mailbox_user, box))
            else:
                logger.debug("rc file for '%s' user is not changed", mailbox_user, extra=context)

            if os.path.isfile(os.path.join(rc_path, 'stop')):
                logger.debug("Getmail is Stopped, remove /etc/getmail/stop to reactivate", extra={'user': '-'})
                sys.exit()
            else:
                subprocess.call(['/usr/bin/getmail', '-g', rc_path, '-r', rc_file_name])
