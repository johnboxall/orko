         .-""""-.
        / -   -  \
       |  .-. .- |
       |  \o| |o (
       \     ^    \
        '.  )--'  /
         '-...-'`

# Orko

Orko is a CLI for analysing Pull Request metadata for users and organizations on
GitHub.

## Install

    git clone git@github.com:mobify/orko.git
    cd orko
    make install

## Usage

Orko fetches and analyses Pull Request metadata from GitHub.

    $ . venv/bin/activate && python orko/orko.py
    GitHub Username: johnboxall
    GitHub Password:
    Query Github by (1) Repo, (2) Organization: 2
    GitHub Organization: mobify
    +-----------------+-----+-------------------+----------------------+----------------------+
    | User            | #   | % Merged Same Day | Median to Merge      | Average to Merge     |
    +-----------------+-----+-------------------+----------------------+----------------------+
    ...