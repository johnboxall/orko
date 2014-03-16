import argparse
import csv
import os
import sys

import prettytable

import cli
import client
import utils


class Outputs:
    TABLE = 'table'
    CSV = 'csv'

# FIXME: Move sorting up to allow sorting by columns other than key?
class Groups:
    HOUR = 'hour'
    MONTH = 'month'
    WEEKDAY = 'weekday'
    USER = 'user'

def get_group_fn(group):
    return ({
        Groups.HOUR: utils.bucket_by_hour,
        Groups.MONTH: utils.bucket_by_month,
        Groups.WEEKDAY: utils.bucket_by_weekday,
        Groups.USER: utils.bucket_by_user,
    }).get(group)

# FIXME: Allow customizing which repos you don't want data on.
# class Filters:
#     pass



def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("auth", help="Github auth, <username>:<password>")
    parser.add_argument("reponame", help="The reponame, <username>/<repo>",
                        default="mobify/portal_app")
    parser.add_argument("-g", "--group",
                        help="grouping mode <[user]|hour|weekday|month>",
                        default=Groups.USER)
    parser.add_argument("-f", "--format", help="output format <[table]|csv>",
                        default=Outputs.TABLE)
    options = parser.parse_args()
    return options


def main():
    options = parse()

    username, password = options.auth.split(":", 2)
    g = client.DiskCacheGitHubClient(username, password)

    data = []
    for reponame in options.reponame.split(","):
        data.extend(g.pull_requests(reponame))


    pulls = utils.process_pull_request(data)

    bucket_fn = get_group_fn(options.group)
    buckets = bucket_fn(pulls)

    columns = [
        options.group.title(),
        "#",
        "% Merged Same Day",
        "Median to Merge",
        "Average to Merge",
    ]

    if options.format == Outputs.CSV:
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
        return

    # The default case, options.format == Output.TABLE
    table = prettytable.PrettyTable(columns, align="l")
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

if __name__ == '__main__':
    main()
    sys.exit()