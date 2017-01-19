Postfix - Getmail connector
===========================

This program permits to use PostfixAdmin (http://postfixadmin.sourceforge.net/) to create Getmail (http://pyropus.ca/software/getmail/) configuration files.
When program is executed it compares modification time of getmailrc file and modification time of the record in database.
If getmailrc file is outdated it will be recreated with new values.


Installation
============
* Install required modules (In this example PostfixAdmin uses MySQL database.)::

    pip install pony
    pip install jinja2
    pip install PyMySQL

.. note:: Script is tested with **Python 3.4** but it should work with **Python 2.6+** also.
         In case both of Python versions are installed you probably need to use pip3 instead of pip

* Download (clone) this program::
    
    git clone https://github.com/andreinl/getmail_postfix.git
    
* Create config.py. It should look like this::

    from pony import orm

    debug = False

    host = 'localhost'
    db = 'postfix'
    user = 'postfixadmin'
    passwd = '<postfixadmin password>'

    tmpl_dir = '/opt/getmail_postfix'
    rc_path = '/etc/getmail'
    base_path = '/var/vmail/'

    database = orm.Database('mysql', host=host, user=user, passwd=passwd, db=db)


In this example Getmail rc files are in */etc/getmail* and emails are in */var/vmail/*.
Program and all its files are in */opt/postfix_getmail*

* create /etc/cron.10min and add in /etc/crontab this line::

    */10 *  * * *   root    cd / && run-parts --report /etc/cron.10min

* create soft link to getmail_postfix.py::

    cd /etc/cron.10min
    ln -s /opt/getmail_postfix/getmail_postfix.py getmail_postfix

* make getmail_postfix.py executable::

    chmod +x /opt/getmailpostfix/getmail_postfix.py

