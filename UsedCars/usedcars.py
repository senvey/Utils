'''
Created on May 31, 2012

@author: William
'''

from string import punctuation
import httplib
import urllib
import re
import time
import os

INTERVAL = 60 # search interval in seconds
HOST = 'orangecounty.craigslist.org'
REQUEST = 'http://orangecounty.craigslist.org/search/cto?query=%s&srchType=T&minAsk=%d&maxAsk=%d&hasPic=1'
TARGETS = {'honda': ('accord', 'civic'), 'toyota': ('camry', 'corolla')}
SHORTCUTS = ('salvage', 'stick', 'manual', 'coupe')
PRICE = (4000, 8000)
MILEAGE = (1000, 150000)

def cars(make, month=None, day=None):
    conn = httplib.HTTPConnection(HOST)
    conn.request('GET', REQUEST % (make, PRICE[0], PRICE[1]))
    resp = conn.getresponse()
    t = resp.read()
    
    _, cur_month, cur_day, _, _ = time.ctime().split()
    if not month: month = cur_month
    if not day: day = cur_day
    pattern = '%s %s - <a href="(?P<url>[\w:/.]+)">(?P<title>[^\n]+)' % (month, day)
    prog = re.compile(pattern)
    
    m = prog.search(t)
    while m:
        url = m.group('url')
        title = m.group('title')
        index = t.find(url) # do not use title in case two titles are identical
        m = prog.search(t[index:])
        
        # year should not less than 2003
        if re.search('[\s>]?1\d{3}\s', title) or title.find('2000') > -1 \
            or title.find('2001') > -1 or title.find('2002') > -1: continue
#        print url, title
        
        for target in TARGETS[make]:
            if title.lower().find(target) > -1:
                yield url


def sift(desc):
    # definitely do not want to buy
    for s in SHORTCUTS:
        if desc.find(s): return False
    
    words = desc.lower().translate(None, punctuation).split()
    
    #===========================================================================
    # MILEAGE
    #===========================================================================
    try:
        index = words.index('miles')
    except:
        return False
    miles = words[index - 1]
    miles = miles.replace(',', '').replace('x', '0').replace('k', '000')
    try:
        miles = int(miles)
    except:
        # try once with one word forward
        miles = words[index - 2]
        miles = miles.replace(',', '').replace('x', '0').replace('k', '000')
        try:
            miles = int(miles)
        except: return False
    if miles < MILEAGE[0] or miles > MILEAGE[1]: return False
    
    return True


def isduplicate(url):
    _, month, day, _, _ = time.ctime().split()
    filename = 'usedcars/archive_%s_%s.txt' % (month, day)
    if os.path.exists(filename):
        with open(filename) as urls:
            for u in urls:
                if url in u: return True
    with open(filename, 'a') as urls:
        urls.write(url + '\n')
    return False


def notify(url, desc):
    '''
    http://docs.python.org/library/email-examples.html
    '''
    
    print 'Found one:', url
    with open('credentials.txt') as cred: 
        server = cred.readline().strip()
        mail_addr = cred.readline().strip()
        username = cred.readline().strip()
        password = cred.readline().strip()
    
    # Import smtplib for the actual sending function
    import smtplib
    # Import the email modules we'll need
    from email.mime.text import MIMEText
    
    # Create a text/plain message
    msg = MIMEText(url + '\n\n' + desc)
    msg['Subject'] = 'New car discovered!'
    msg['From'] = mail_addr
    msg['To'] = mail_addr
    
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP(server)
    s.starttls()
    s.login(username, password)
    s.sendmail(mail_addr, [mail_addr], msg.as_string())
    s.quit()


def search():
    print 'Searching...', time.ctime()
    
    for make in TARGETS.iterkeys():
        for url in cars(make):
            page = urllib.urlopen(url)
            desc = page.read()
            if sift(desc) and not isduplicate(url):
                notify(url, desc)


if __name__ == '__main__':
    
    while True:
        search()
        time.sleep(INTERVAL)
    
    print 'DONE!'





