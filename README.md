                 __
                /\ \
      ___   _ __\ \ \/'\     ___
     / __`\/\`'__\ \ , <    / __`\
    /\ \L\ \ \ \/ \ \ \\`\ /\ \L\ \
    \ \____/\ \_\  \ \_\ \_\ \____/
     \/___/  \/_/   \/_/\/_/\/___/

# Orko

Orko is a CLI for analyzing Pull Request metadata from GitHub.

## Install

The latest development version can be installed directly from GitHub:

    pip install --upgrade https://github.com/johnboxall/orko/tarball/master

## Usage

Orko queries GitHub for Pull Request metadata for one or more repos and then
groups the data by repo, user, hour, weekeday or month.

    orko --auth <username>:<password> user/reponame

Orko fetches Pull Requests serially which can be a bit slow if you're working with
a repo with hundreds of PRs. To store them to disk, use the `DiskCacheClient`:

    orko --client orko.github.DiskCacheClient

### Two-Factor Auth

If two-factor auth is enabled for your GitHub account Orko won't be able to
fetch your data with just your password. Instead, generate a personal access
token with "repo" access, and use that as your password: https://github.com/settings/tokens/new
