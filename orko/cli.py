#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import argparse
import csv
import getpass
import os
import sys

import prettytable

from orko import github
from orko import util


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
    "user:hashed",
    "repo"
)

AUTH_HELP = "Github auth in the format <user>:<password>"
GROUP_HELP = "Grouping mode, one of: user, repo, hour, weekday, month. Defaults to user."
OUTPUT_HELP = "Output format, one of: table, csv. Defaults to table."
REPO_HELP = "A list of full repository names to query in the format <user|org>/<repo>"
CLIENT_HELP = "Github client, one of: orko.github.Client, orko.github.DiskCacheClient"

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", type=parse_auth, default=None, help=AUTH_HELP)
    parser.add_argument("-g", "--group", default="user", help=GROUP_HELP)
    parser.add_argument("-f", "--format", default="table", help=OUTPUT_HELP)
    parser.add_argument("-c", "--client", default=None, help=CLIENT_HELP)
    parser.add_argument("reponames", nargs="*", help=REPO_HELP)
    return parser.parse_args()

def parse_auth(auth_str):
    auth = tuple(auth_str.split(":", 2))
    if len(auth) == 2:
        return auth
    raise argparse.ArgumentTypeError(AUTH_HELP)

def auth_from_input():
    username = raw_input("GitHub Username: ")
    password = getpass.getpass("GitHub Password: ")
    auth = (username, password)
    return auth

def groups_for_group_option(group, pr_list):
    if group == 'repo':
        return pr_list.group_by_repo()
    if group == 'user':
        return pr_list.group_by_user()
    if group == 'user:hashed':
        return pr_list.group_by_hashed_user()
    if group == 'hour':
        return pr_list.group_by_hour()
    if group == 'weekday':
        return pr_list.group_by_weekday()
    if group == 'month':
        return pr_list.group_by_month()
    raise


###
# Output
###

def output_csv(columns, groups):
    writer = csv.writer(sys.stdout)
    writer.writerow(columns)

    for group_key, pr_list in groups:
        row = [
            group_key,
            len(pr_list),
            pr_list.merged_same_day_percent(),
            int(pr_list.median_duration().total_seconds()),
            int(pr_list.average_duration().total_seconds())
        ]
        writer.writerow(row)

def output_table(columns, groups):
    table = prettytable.PrettyTable(columns)
    table.align = "l"

    for group_key, pr_list in groups:
        row = [
            group_key,
            len(pr_list),
            pr_list.merged_same_day_percent(),
            util.timedelta_to_human(pr_list.median_duration()),
            util.timedelta_to_human(pr_list.average_duration()),
        ]
        table.add_row(row)

    print table


###
# Main
###

def main():
    options = parse()
    auth = options.auth or auth_from_input()
    github_client = github.get_client(auth, options.client)

    reponames = options.reponames
    if not len(reponames):
        query = raw_input("Query Github by (1) Repo, (2) Organization: ")
        if query == "1":
            reponame = raw_input("GitHub Repo: ")
            reponames = [reponame]
        else:
            org = raw_input("Github Organization: ")
            reponames = [i["full_name"] for i in github_client.organization_repos(org)]

    prlist = util.prlist_for_reponames(github_client, reponames)
    prlist = prlist.filter_unmerged()
    groups = groups_for_group_option(options.group, prlist)

    columns = [
        options.group.title(),
        "#",
        "% Merged Same Day",
        "Median to Merge",
        "Average to Merge",
    ]

    if options.format == 'csv':
        return output_csv(columns, groups)

    output_table(columns, groups)


if __name__ == '__main__':
    main()