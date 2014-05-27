import collections
import datetime
import hashlib

import ago
import pytz
import requests
import tzlocal


DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


class PRList(object):
    def __init__(self, prs=None):
        self.prs = prs or []

    def __len__(self):
        return len(self.prs)

    def __iter__(self):
        return iter(self.prs)

    def filter_unmerged(self):
        return PRList([pr for pr in self if pr["merged_at"] is not None])

    def group_by_date(self, group_key_date_format):
        groups = {}
        for pr in self:
            group_key = iso8601_to_local_datetime(pr["created_at"]).strftime(group_key_date_format)
            if group_key not in groups:
                groups[group_key] = PRList()
            groups[group_key].prs.append(pr)
        return groups

    def sorted_group_by_date(self, group_key_date_format, group_key_sort_fn=str.lower):
        groups = self.group_by_date(group_key_date_format)
        sorted_groups = sorted(
            groups.iteritems(),
            key=lambda t: group_key_sort_fn(t[0])
        )
        return sorted_groups

    def group_by_hour(self):
        return self.sorted_group_by_date("%H", str.lower)

    def group_by_weekday(self):
        groups = self.group_by_date("%A")
        sorted_groups = [(day, groups[day]) for day in DAYS if day in groups]
        return sorted_groups

    def group_by_month(self):
        return self.sorted_group_by_date("%Y-%m")

    def group_by_user(self):
        groups = {}
        for pr in self:
            group_key = pr["user"]["login"]
            if group_key not in groups:
                groups[group_key] = PRList()
            groups[group_key].prs.append(pr)
        sorted_groups = sorted(groups.iteritems(), key=lambda t: len(t[1]))
        return sorted_groups

    def group_by_hashed_user(self):
        groups = {}
        for pr in self:
            group_key = hashlib.md5(pr["user"]["login"]).hexdigest()[0:8]
            if group_key not in groups:
                groups[group_key] = PRList()
            groups[group_key].prs.append(pr)
        sorted_groups = sorted(groups.iteritems(), key=lambda t: len(t[1]))
        return sorted_groups

    def group_by_repo(self):
        groups = {}
        for pr in self:
            group_key = pr["base"]["repo"]["full_name"]
            if group_key not in groups:
                groups[group_key] = PRList()
            groups[group_key].prs.append(pr)
        sorted_groups = sorted(groups.iteritems(), key=lambda t: len(t[1]))
        return sorted_groups

    def average_duration(self):
        return sum(
            (pr_duration(pr) for pr in self),
            datetime.timedelta(0)
        ) / len(self)

    def median_duration(self):
        return sorted(
            (pr_duration(pr) for pr in self)
        )[len(self) / 2]

    def merged_same_day(self):
        return sum(
            iso8601_to_local_datetime(pr["created_at"]).date() == \
            iso8601_to_local_datetime(pr["merged_at"]).date()
            for pr in self
        )

    def merged_same_day_percent(self):
        return "%2.2f" % (float(self.merged_same_day()) / float(len(self)) * 100)


def prlist_for_reponames(github_client, reponames):
    '''
    Returns a `PRList` instance given a list of `reponames`.

    '''
    prs = []
    try:
        for reponame in reponames:
            prs.extend(github_client.pull_requests(reponame))
    except requests.exceptions.HTTPError:
        print "Error fetching data for '%s'. Check the reponame and your GitHub " \
              "credentials and permissions." % (reponame)
        raise
    return PRList(prs)


###
# Date Helpers
###

def pr_duration(pr):
    '''
    Returns a `timedelta` duration for a Pull Request.

    '''
    created_at = iso8601_to_local_datetime(pr['created_at'])
    merged_at = iso8601_to_local_datetime(pr['merged_at'])
    return merged_at - created_at

def iso8601_to_local_datetime(str):
    '''
    Returns local `datetime` instance for a UTC ISO 8601 formatted string `str`.

    '''
    utc_dt = datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
    local_dt = utc_dt.astimezone(tzlocal.get_localzone())
    return local_dt

def timedelta_to_human(td):
    '''
    Returns a vaguely readable string for a `timedelta` instance.

    '''
    s = ago.human(td, precision=2, past_tense='{}')
    return ','.join(s.split(',', 3)[0:2])