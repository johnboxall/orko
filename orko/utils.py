import collections
import datetime

import ago
import pytz
import tzlocal

###
# Pull Request Utils
###

def process_pull_request(data):
    '''
    Process a list of raw Pull Requests from GitHub into something a bit more
    useable. Mostly:

    * Dates to localtimes
    * Discard duplicate IDs (not sure where they are coming from)
    * Discard unmerged PRs

    '''
    ids = set()
    pulls = []
    for i in data:
        # Skip PRs that are not merged.
        if not i['merged_at']:
            continue

        # Skip PRs that have been seen before.
        if i['id'] in ids:
            continue

        created_at = iso8601_to_local_datetime(i['created_at'])
        merged_at = iso8601_to_local_datetime(i['merged_at'])
        # FIXME: Should this include non-working days eg. Holidays + Weekends?
        duration = merged_at - created_at
        duration_seconds = duration.total_seconds()

        # Skip PRs that were merged quickly or very slowly.
        # if not (datetime.timedelta(days=1) < duration < datetime.timedelta(days=5)):
        #     continue

        # Skip PRs not made on a work day. 6 = Saturday, 7 = Sunday.
        if created_at.isoweekday() in [6, 7]:
            continue

        # Skip PRs not made within working hours. 6a - 6p.
        if not (6 < created_at.hour < 18):
            continue

        ids.add(i['id'])

        pull = {
            "created_at": created_at,
            "merged_at": merged_at,
            "duration": duration,
            "duration_seconds": duration_seconds,
            "title": i["title"],
            "user": i["user"]["login"],
        }

        pulls.append(pull)

    return pulls


def interesting(pulls):
    '''
    Return a dict of interesting things about a list of Pull Requests.

    '''
    times = sorted(p["duration"] for p in pulls)

    median = times[len(times) / 2]
    # Passing datetime.timedelta(0) as the start value makes sum work on tds.
    average = sum(times, datetime.timedelta(0)) / len(times)

    # Number of PRs merged on the same day they were created.
    merged_same_day = sum(p["created_at"].date() == p["merged_at"].date() for p in pulls)

    length = len(pulls)

    interesting = {
        "times": times,
        "median": median,
        "average": average,
        "merged_same_day": merged_same_day,
        "merged_same_day_percent": float(merged_same_day) / float(length),
        "length": length,
    }

    return interesting


###
# Bucketing
###

def bucket(pulls, bucket_key_fn):
    '''
    Returns a dict of pull requests bucketed by `bucket_key_fn`.

    '''
    buckets = collections.defaultdict(list)
    for pull in pulls:
        bucket_key = bucket_key_fn(pull)
        buckets[bucket_key].append(pull)
    return {bucket_key: interesting(pulls) for bucket_key, pulls in buckets.items()}

def bucket_by_user(pulls):
    buckets = bucket(pulls, lambda pull: pull["user"])
    sorted_buckets = sorted(buckets.iteritems(), key=lambda t: t[1]["length"])
    return sorted_buckets

def bucket_by_date(pulls, bucket_key_format):
    return bucket(pulls, lambda pull: pull["created_at"].strftime(bucket_key_format))

def sorted_bucket_by_date(pulls, bucket_key_format, bucket_key_sort_fn=str.lower):
    buckets = bucket_by_date(pulls, bucket_key_format)
    sorted_buckets = sorted(buckets.iteritems(), key=lambda t: bucket_key_sort_fn(t[0]))
    return sorted_buckets

def bucket_by_hour(pulls):
    return sorted_bucket_by_date(pulls, "%H", str.lower)

def bucket_by_month(pulls):
    return sorted_bucket_by_date(pulls, "%Y-%m")

def bucket_by_weekday(pulls):
    buckets = bucket_by_date(pulls, "%A")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return [(day, buckets[day]) for day in days if day in buckets]


###
# Date Helpers
###

def iso8601_to_local_datetime(str):
    '''
    Returns local datetime instance for a UTC ISO 8601 formatted string `str`.

    '''
    utc_dt = datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
    local_dt = utc_dt.astimezone(tzlocal.get_localzone())
    return local_dt


def timedelta_to_human(td):
    '''
    Returns a vaguely readable string for a timedelta instance.

    '''
    s = ago.human(td, precision=2, past_tense='{}')
    return ','.join(s.split(',', 3)[0:2])