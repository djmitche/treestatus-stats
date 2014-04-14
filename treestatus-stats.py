import requests
import datetime
import argparse

from matplotlib import pyplot as plt
from matplotlib.dates import date2num


def main(tree):
    response = requests.get('https://treestatus.mozilla.org/%s/logs?format=json&all=1' % tree, verify=False)
    results = response.json()
    delta = datetime.timedelta(0)
    closed = None
    closed_reason = None
    dates = {}
    month = {}
    total = datetime.timedelta(0)
    Added = None
    for item in reversed(results['logs']):
        if item['action'] == 'closed':
            if closed is not None:
                continue
            closed = datetime.datetime.strptime(item['when'], "%Y-%m-%dT%H:%M:%S")
            closed_reason = item['tags'][0] if len(item['tags']) > 0 else 'no reason'
        elif item['action'] == 'open' or item['action'] == 'approval require':
            if closed is None:
                continue
            opened = datetime.datetime.strptime(item['when'], "%Y-%m-%dT%H:%M:%S")
            delta = opened - closed

            if closed.date().isoformat() in dates:
                try:
                    dates[closed.date().isoformat()]['total'] = dates[closed.date().isoformat()]['total'] + delta
                    dates[closed.date().isoformat()][closed_reason] = dates[closed.date().isoformat()][closed_reason] + delta
                except:
                    dates[closed.date().isoformat()][closed_reason] = delta
            else:
                dates[closed.date().isoformat()] = {'total': delta, closed_reason: delta}

            year_month = "%s-%s" % (closed.date().year, closed.date().month if closed.date().month >= 10 else '0%s' % closed.date().month)

            if year_month not in ['2012-06', '2012-07']:
                if year_month in month:
                    month[year_month]['total'] = month[year_month]['total'] + delta
                    try:
                        month[year_month][closed_reason] = month[year_month][closed_reason] + delta
                    except:
                        month[year_month][closed_reason] = delta
                else:
                    month[year_month] = {'total': delta, closed_reason: delta}

                total += delta
            closed = None
            closed_reason = None
        elif item['action'] == 'added':
            Added = item['when']
            print "Added on :%s" % item['when']

    print "Tree has been closed for a total of %s since it was created on %s" % (total, Added)
    _print_dict(month)
    return month, dates


def _print_dict(_dict):
    for k in sorted(_dict.keys()):
        if type(_dict[k]) == dict:
            print "%s" % k
            for reason in sorted(_dict[k].keys()):
                print "\t %s: %s" % (reason, _dict[k][reason])
        else:
            print "%s : %s" % (k, _dict[k])


def backout():
    import subprocess
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
    p = subprocess.Popen("hg log -l 100000", shell=True, stdout=subprocess.PIPE)
    data = p.communicate()
    results = {}
    total_pushes = {}
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
            if d not in total_pushes:
                total_pushes[d] = 1
            else:
                total_pushes[d] = total_pushes[d] + 1

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
              '2013-09': 0,
              '2013-10': 0,
              '2013-11': 0,
              '2013-12': 0,
              '2014-01': 0,
              '2014-02': 0,
              '2014-03': 0,
              '2014-04': 0}
    total_pushes_pm = totals.copy()
    for item in results:
        for bucket in totals:
            if bucket in item:
                totals[bucket] += len(results[item])
    for item in total_pushes:
        for bucket in total_pushes_pm:
            if bucket in item:
                total_pushes_pm[bucket] += total_pushes[item]
    print('\nBackouts per month')
    _print_dict(totals)
    print('\n\nPushes per month')
    _print_dict(total_pushes_pm)
    return totals, total_pushes_pm

def plot(tree):
    closure_months, closure_dates = main(tree)
    backouts, backouts_pm = backout()

    fig, axes = plt.subplots()

    # Generate Closure subplot
    c_data = [(datetime.datetime.strptime(k, "%Y-%m"), closure_months[k]['total']) for k in sorted(closure_months.keys())]

    x = [date2num(date) for (date, value) in c_data]
    y = [value.total_seconds() / 3600 for (date, value) in c_data]

    # Plot the data as a red line with round markers
    plt.plot(x, y, 'r', label='Closure total')

    # Backout Data
    b_data = [(datetime.datetime.strptime(k, "%Y-%m"), backouts[k]) for k in sorted(backouts.keys())]

    x1 = [date2num(date) for (date, value) in b_data]
    y1 = [value for (date, value) in b_data]

    plt.plot(x1, y1, 'b', label='Backouts per month')

    # Set the xtick labels to correspond to just the dates you entered.
    plt.xticks(x,
               [date.strftime("%Y-%m") for (date, value) in c_data],
               rotation=45
               )
    plt.legend()
    plt.savefig('test.jpg', dpi=200)

def plot_backout_vs_push():

    backouts, pushes = backout()

    c_data = [(datetime.datetime.strptime(k, "%Y-%m"), pushes[k]) for k in sorted(pushes.keys())]

    x = [date2num(date) for (date, value) in c_data]
    y = []
    for backot in backouts.keys():
        try:
            y.append(pushes[backot] / backouts[backot])
        except:
            y.append(0)
    fig, graph = plt.subplots()
    # Plot the data as a red line with round markers
    graph.plot(x, y, 'r', label="Backouts vs Commit ratio")
    graph.set_ylim(min(y) - 1, max(y) + 1)

    # Set the xtick labels to correspond to just the dates you entered.
    plt.xticks(x,
                [date.strftime("%Y-%m") for (date, value) in c_data],
                rotation=45
                )
    plt.legend()
    plt.savefig('backout_vs_pushes.jpg', dpi=200)

def plot_backout_reasons(tree):
    closure_months, closure_dates = main(tree)

    fig, axes = plt.subplots()
    x = []
    y = {'no reason': [],
         'checkin-test': [],
         'checkin-compilation': [],
         'infra': [],
         'other': [],
         'planned': [],
         'total': [],
         'backlog': [],
         'checkin-test': []}

    c_data = [(datetime.datetime.strptime(k, "%Y-%m"), closure_months[k]) for k in sorted(closure_months.keys())]
    x = [date2num(date) for (date, value) in c_data]
    for data in c_data:
        # We need to make a sparse array so we can have the 2 arrays the same length when plotting
        not_filled = [k for k in y.keys() if k not in data[1].keys()]
        for nf in not_filled:
            y[nf].append(0)
        #show me the data
        for _x in data[1].keys():
            y[_x].append(data[1][_x].total_seconds() / 3600)

    plt.xticks(x,
               [date.strftime("%Y-%m") for (date, value) in c_data],
               rotation=45
               )
    axes.set_ylabel("Closure time (in hours)")
    # Draw each line
    for keys in y.keys():
        plt.plot(x, y[keys], label=keys)

    # loc = 2 means put the legend on the top left
    plt.legend(loc=2)
    plt.savefig('%s-closures.jpg' % tree, dpi=200)



# Parser and running code
parser = argparse.ArgumentParser(description="Collect and print Treestatus stats")
parser.add_argument('--tree', dest='tree',
                    choices=['mozilla-inbound', "mozilla-aurora", "mozilla-beta",
                             'mozilla-central', 'fx-team', 'b2g-inbound'],
                    help='Tree that you wish to use')
parser.add_argument('--backout', dest='backout', action='store_true',
                    help='Show all backout data.')
parser.add_argument('--generate', dest='generate', action='store_true',
                    help='Generate a plot of data')
parser.add_argument('--backout_vs_pushes', dest='backout_vs_pushes', action='store_true',
                    help='Generate a plot of data for backouts vs pushes')
parser.add_argument('--closures', dest='closures', action='store_true',
                    help='Generate a plot of data')
args = parser.parse_args()

if args.tree is not None and args.generate is False and args.closures is False:
    main(args.tree)
if args.tree is not None and args.closures:
    plot_backout_reasons(args.tree)
if args.backout is True and args.generate is False:
        backout()
if args.generate is True and args.closures is False:
    if args.tree is None:
        argparse.ArgumentParser.error('Please pass in the tree')
    plot(args.tree)
if args.backout_vs_pushes is True:
    plot_backout_vs_push()
