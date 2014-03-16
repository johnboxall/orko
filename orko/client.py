import hashlib
import itertools
import json
import os

import requests


class GitHubClient(object):
    base_uri = 'https://api.github.com/'
    # Request the V3 API.
    base_headers = {"Accept": "application/vnd.github.v3+json"}

    def __init__(self, username, password):
        self.auth = (username, password)

    def request(self, path, params=None, method='GET', headers=None):
        url = self.base_uri + path
        headers = dict(self.base_headers, **(headers or {}))
        response = requests.request(method, url,
                                    params=params,
                                    headers=headers,
                                    auth=self.auth)
        response.raise_for_status()
        return response.json()

    def repos(self):
        '''
        Returns a list of repositories for the authenticated user.

        '''
        return client.request('repos')

    def organization_repos(self, org):
        return client.request('orgs/%s/repos' % org)


    def pull_requests(self, reponame):
        '''
        Returns a list of all Pull Requests for `reponame`.

        '''
        path = 'repos/%s/pulls' % reponame

        params = {
            "per_page": "100",
            "state": "all",
            "sort": "created",
            "direction": "desc",
        }

        pulls = []
        for page in itertools.count(1):
            data = self.request(path, params=dict(params, page=str(page)))
            if not len(data):
                break

            pulls.extend(data)

        return pulls


class DiskCacheGitHubClient(GitHubClient):
    cache_dir = '.cache'

    def __init__(self, username, password):
        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

        super(DiskCacheGitHubClient, self).__init__(username, password)

    def request(self, path, params=None, method='GET', headers=None):
        seed = path + '|' + '|'.join((params or {}).values())
        print seed
        cache_key = hashlib.md5(seed).hexdigest()

        filename = os.path.join(self.cache_dir, cache_key)

        if os.path.isfile(filename):
            return json.loads(open(filename).read())

        data = super(DiskCacheGitHubClient, self).request(path, params, method, headers)
        with open(filename, "w") as f:
            f.write(json.dumps(data))
        return data