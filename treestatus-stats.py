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


parser = argparse.ArgumentParser(description="Collect and print Treestatus stats")
parser.add_argument('--tree', dest='tree',
                    choices=['mozilla-inbound', "mozilla-aurora", "mozilla-beta",
                             'mozilla-central', 'fx-team', 'b2g-inbound'],
                    help='Tree that you wish to use')

args = parser.parse_args()
if args.tree is not None:
    main(args.tree)
