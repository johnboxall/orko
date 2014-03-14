'''
A script for calculating interesting things about a repo's Pull Requests.

Install:
    mkdir orko
    cd orko
    # drop the script in there
    virtualenv venv
    source venv/bin/activate
    pip install ago pytz requests

Usage:

    client.py <reponame> <username>:<password>
    client.py mobify/portal_app john:sup

'''
import argparse
import collections
import datetime
import json
import os

import ago
import pytz
import requests


UTC = pytz.UTC


class GitHubClient(object):
    base = 'https://api.github.com'

    def __init__(self, username, password):
        self.auth = (username, password)

    def request(self, path, params=None, method='GET'):
        url = self.base + path
        # Request the V3 API.
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.request(method, url,
                                    params=params,
                                    headers=headers,
                                    auth=self.auth)
        return response

    def pull_requests(self, reponame):
        '''
        Returns a list of all Pull Requests for `reponame`.

        '''
        path = '/repos/%s/pulls' % reponame

        params = {
            "state": "all",
            "per_page": 100
        }

        pulls = []
        page = 0
        while True:
            response = client.request(path, params=dict(params, page=page))
            if response.status_code != 200:
                break

            page_pulls = response.json()
            if not len(page_pulls):
                break

            page = page + 1
            pulls.extend(response.json())

        return pulls



def interesting(pulls):
    '''
    Return a set dict of interesting information about a list of pull requests.

    '''
    buckets = collections.OrderedDict()

    ids = set()

    for pull in pulls:
        created_at = iso8601_to_datetime(pull['created_at'])
        key = "%s-%s" % (created_at.year, str(created_at.month).zfill(2))
        if key not in buckets:
            buckets[key] = []

        # For some reason, we're seeing the same IDs show up.
        if pull['id'] in ids:
            continue
        ids.add(pull['id'])

        buckets[key].append(pull)

    interesting = collections.OrderedDict()
    for key, pulls in buckets.iteritems():
        times = []
        for pull in pulls:
            if not pull['closed_at']:
                continue

            t = iso8601_to_datetime(pull['closed_at']) - iso8601_to_datetime(pull['created_at'])
            times.append(t)

        times = sorted(times)
        median = times[len(times) / 2]
        # giving datetime.timedelta(0) as the start value makes sum work on tds
        average = sum(times, datetime.timedelta(0)) / len(times)

        interesting[key] = {
            "times": times,
            "median": median,
            "average": average
        }

    return interesting


def iso8601_to_datetime(str):
    '''
    Returns UTC datetime instance for a UTC ISO 8601 formatted string `str`.

    '''
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)

def timedelta_to_human(td):
    s = ago.human(td, precision=2, past_tense='{}')
    return ','.join(s.split(',', 3)[0:2])


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="The repo, <username>/<repo>", default="mobify/portal_app")
    parser.add_argument("auth", help="Github auth, <username>:<password>")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = cli()
    repo = args.repo
    username, password = args.auth.split(":", 2)

    filename =  "%s.json" % repo.replace("/", ".")

    if os.path.isfile(filename):
        print 'Using Pulls from disk.'
        pulls = json.loads(open(filename).read())
    else:
        print 'Fetching Pulls from GitHub.'
        client = GitHubClient(username, password)
        pulls = client.pull_requests(repo)
        with open(filename, "w") as f:
            f.write(json.dumps(pulls))

    buckets = interesting(pulls)

    print "YYYY-MM\t#\tMedian\t\t\tAverage"
    for key, data in buckets.iteritems():
        median = timedelta_to_human(data["median"]).ljust(23)
        average = timedelta_to_human(data["average"]).ljust(23)

        print "%s\t%s\t%s\t%s" % (key, len(data["times"]), median, average)