import hashlib
import itertools
import json
import os


class GitHubClient(object):
    '''
    Simple GitHub client. Pass in a `requests.Session` with basic auth or use
    OAuth.

    '''
    base_uri = 'https://api.github.com/'
    # Request the V3 API.
    base_headers = {"Accept": "application/vnd.github.v3+json"}

    def __init__(self, session):
        self.session = session

    def request(self, path, params=None, method='GET', headers=None):
        url = self.base_uri + path
        headers = dict(self.base_headers, **(headers or {}))

        response = self.session.request(method, url,
                                        params=params,
                                        headers=headers)
        response.raise_for_status()
        return response.json()

    def paged_request(self, path, params=None, method='GET', headers=None,
                      page=1, per_page=100):
        '''
        Requests all the items for `path` starting at `page` and paging up until
        no more items are found.

        '''
        params = params or {}
        params["per_page"] = str(per_page)

        items = []
        for page_number in itertools.count(page):
            data = self.request(path, params=dict(params, page=str(page_number)))

            length = len(data)

            if not length:
                break

            items.extend(data)

            if length != per_page:
                break

        return items

    def repos(self):
        '''
        Returns a list of repositories for the authenticated user.

        '''
        return self.paged_request('repos')

    def user_repos(self, username):
        '''
        Returns a list of repos for the user, `username`.

        '''
        return self.paged_request('user/%s/repos' % username)


    def organization_repos(self, org):
        '''
        Returns a list of repos for the organization, `org`.

        '''
        return self.paged_request('orgs/%s/repos' % org)

    def pull_requests(self, reponame):
        '''
        Returns a list of all Pull Requests for the repository, `reponame`.

        '''
        params = {
            "state": "all",
            "sort": "created",
            "direction": "desc"
        }

        return self.paged_request('repos/%s/pulls' % reponame, params=params)


class DiskCacheGitHubClient(GitHubClient):
    '''
    A GitHub client that caches responses to disk.

    '''
    cache_dir = '.cache'

    def __init__(self, session):
        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

        super(DiskCacheGitHubClient, self).__init__(session)

    def request(self, path, params=None, method='GET', headers=None):
        seed = path + '|' + '|'.join((params or {}).values())
        cache_key = hashlib.md5(seed).hexdigest()

        filename = os.path.join(self.cache_dir, cache_key)

        if os.path.isfile(filename):
            return json.loads(open(filename).read())

        data = super(DiskCacheGitHubClient, self).request(path, params, method, headers)
        with open(filename, "w") as f:
            f.write(json.dumps(data))
        return data