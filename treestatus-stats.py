import requests
import datetime
import argparse


def main(tree):
    response = requests.get('https://treestatus.mozilla.org/%s/logs?format=json&all=1' % tree, verify=False)
    results = response.json()
    delta = datetime.timedelta(0)
    closed = None
    dates = {}
    month = {}
    total = datetime.timedelta(0)
    Added = None
    for item in reversed(results['logs']):
        if item['action'] == 'closed':
            if closed is not None:
                continue
            closed = datetime.datetime.strptime(item['when'], "%Y-%m-%dT%H:%M:%S")
        elif item['action'] == 'open' or item['action'] == 'approval require':
            if closed is None:
                continue
            opened = datetime.datetime.strptime(item['when'], "%Y-%m-%dT%H:%M:%S")
            delta = opened - closed

            if closed.date().isoformat() in dates:
                dates[closed.date().isoformat()] = dates[closed.date().isoformat()] + delta
            else:
                dates[closed.date().isoformat()] = delta

            year_month = "%s-%s" % (closed.date().year, closed.date().month)

            if year_month not in ['2012-6', '2012-7']:
                if year_month in month:
                    month[year_month] = month[year_month] + delta
                else:
                    month[year_month] = delta

                total += delta
            closed = None
        elif item['action'] == 'added':
            Added = item['when']
            print "Added on :%s" % item['when']

    print "Tree has been closed for a total of %s since it was created on %s" % (total, Added)
    for k in sorted(month.keys()):
        print "%s : %s" % (k, month[k])

def backout():
    import os, subprocess
    import pdb
    import re
    import sys
    import datetime

    def getmonth(s):
        if s == "Jan":
            return 1
        elif s == "Feb":
            return 2
        elif s == "Mar":
            return 3
        elif s == "Apr":
            return 4
        elif s == "May":
            return 5
        elif s == "Jun":
            return 6
        elif s == "Jul":
            return 7
        elif s == "Aug":
            return 8
        elif s == "Sep":
            return 9
        elif s == "Oct":
            return 10
        elif s == "Nov":
            return 11
        elif s == "Dec":
            return 12
        else:
            print "Unknown month: %s" % s
            sys.exit(1)     

    def parsedate(line):
        elements = line.split(" ")
        month = getmonth(elements[9])
        # Note we don't screw with timezones so this may be off by 1
        day = int(elements[10])
        year = int(elements[12])

        return datetime.date(year, month, day).isoformat()

    #pdb.set_trace()
    p = subprocess.Popen("hg log -l 50000", shell=True, stdout=subprocess.PIPE)
    data = p.communicate()
    results = {}
    lines = data[0].split("\n")

    dateln = re.compile('^date:.*')
    backoutln = re.compile('^summary:.*[b,B]ackout.*')
    backoutln2 = re.compile('^summary:.*[b,B]acked out.*')
    backoutln3 = re.compile('^summary:.*[b,B]ack out.*')

    i = 0
    while i < len(lines):
    #   print lines[i]
        if dateln.match(lines[i]):
            d = parsedate(lines[i])

            # Initialize the list if we need to
            if d not in results:
                results[d] = []

            if (backoutln.match(lines[i+1]) or
                backoutln2.match(lines[i+1]) or
                backoutln3.match(lines[i+1])):
                results[d].append(lines[i+1])
            # Avoid processing the summary line since we already have
            # either we counted it as a backout or we didn't but either way
            # it's done, so skip over it
            i += 1
            
        # Advance to next line
        i += 1

    #print "***********************************************"
    #print results
    #print "***********************************************"

    # Now, output the counts
    totals = {'2012-08': 0,
              '2012-09': 0,
              '2012-10': 0,
              '2012-11': 0,
              '2012-12': 0,
              '2013-01': 0,
              '2013-02': 0,
              '2013-03': 0,
              '2013-04': 0,
              '2013-05': 0,
              '2013-06': 0,
              '2013-07': 0,
              '2013-08': 0,
              '2013-09': 0}
    for item in results:
        for bucket in totals:
            if bucket in item:
                totals[bucket] += len(results[item])

    print totals


parser = argparse.ArgumentParser(description="Collect and print Treestatus stats")
parser.add_argument('--tree', dest='tree',
                    choices=['mozilla-inbound', "mozilla-aurora", "mozilla-beta",
                             'mozilla-central', 'fx-team', 'b2g-inbound'],
                    help='Tree that you wish to use')
parser.add_argument('--backout', dest='backout', action='store_true',
                    help='Show all backout data.')

args = parser.parse_args()

if args.tree is not None:
    main(args.tree)
if args.backout is True:
        backout()

