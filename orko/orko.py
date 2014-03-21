import argparse
import csv
import getpass
import os
import sys

import prettytable
import requests

import client
import utils


###
# Parser
###

OUTPUTS = (
    "table",
    "csv"
)

GROUPS = (
    "hour",
    "month",
    "weekday",
    "user",
    "repo"
)

AUTH_HELP = "Github auth in the format <user>:<password>"
GROUP_HELP = "Grouping mode, one of: user, repo, hour, weekday, month. Defaults to user."
OUTPUT_HELP = "Output format, one of: table, csv. Defaults to table."
REPO_HELP = "A list of full repository names to query in the format <user|org>/<repo>"

def parse_auth(auth_str):
    auth = tuple(auth_str.split(":", 2))
    if len(auth) == 2:
        return auth
    raise argparse.ArgumentTypeError(AUTH_HELP)

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", type=parse_auth, default=None, help=AUTH_HELP)
    parser.add_argument("-g", "--group", default="user", help=GROUP_HELP)
    parser.add_argument("-f", "--format", default="table", help=OUTPUT_HELP)
    parser.add_argument("reponames", nargs="*", help=REPO_HELP)
    return parser.parse_args()


###
# Output
###

def output_csv(columns, buckets):
    writer = csv.writer(sys.stdout)
    writer.writerow(columns)

    for bucket_key, data in buckets:
        row = [
            bucket_key,
            data["length"],
            "%2.2f" % (data["merged_same_day_percent"] * 100),
            int(data["median"].total_seconds()),
            int(data["average"].total_seconds())
        ]
        writer.writerow(row)

def output_table(columns, buckets):
    table = prettytable.PrettyTable(columns)
    table.align = "l"

    for bucket_key, data in buckets:
        row = [
            bucket_key,
            data["length"],
            "%2.2f" % (data["merged_same_day_percent"] * 100),
            utils.timedelta_to_human(data["median"]),
            utils.timedelta_to_human(data["average"]),
        ]
        table.add_row(row)

    print table


###
# Main
###

def main():
    options = parse()

    auth = options.auth
    if auth is None:
        username = raw_input("GitHub Username: ")
        password = getpass.getpass("GitHub Password: ")
        auth = (username, password)

    session = requests.Session()
    session.auth = auth
    github = client.DiskCacheGitHubClient(session)

    reponames = options.reponames
    if not len(reponames):
        query = raw_input("Query Github by (1) Repo, (2) Organization: ")
        if query == "1":
            reponame = raw_input("GitHub Repo: ")
            reponames = [reponame]
        else:
            org = raw_input("Github Organization: ")
            reponames = [i["full_name"] for i in github.organization_repos(org)]

    data = []

    try:
        for reponame in reponames:
            data.extend(github.pull_requests(reponame))
    except requests.exceptions.HTTPError:
        print "Error fetching data for %s. Check the reponame and your GitHub " \
              "credentials and permissions." % (reponame)
        raise

    pulls = utils.process_pull_request(data)

    if options.group == 'hour':
        bucket_fn = utils.bucket_by_hour
    elif options.group == 'weekday':
        bucket_fn = utils.bucket_by_weekday
    elif options.group == 'month':
        bucket_fn = utils.bucket_by_month
    elif options.group == 'repo':
        bucket_fn = utils.bucket_by_repo
    else:
        bucket_fn = utils.bucket_by_user

    buckets = bucket_fn(pulls)

    columns = [
        options.group.title(),
        "#",
        "% Merged Same Day",
        "Median to Merge",
        "Average to Merge",
    ]

    if options.format == 'csv':
        return output_csv(columns, buckets)

    output_table(columns, buckets)


if __name__ == '__main__':
    main()