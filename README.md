# reddit-sedbot

[![PyPI - Version](https://img.shields.io/pypi/v/reddit-sedbot.svg)](https://pypi.org/project/reddit-sedbot)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/reddit-sedbot.svg)](https://pypi.org/project/reddit-sedbot)

-----

**Table of Contents**

- [About](#about)
- [Installation](#installation)
- [License](#license)

## About

This bot parses comments on reddit looking for inline codeblocks of the form `[some sed command]` (e.g. `s/foo/bar/`), and replies to them with the altered contents of the parent comment. To run, create a [praw.ini](https://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html) file and fill it with the details of your (bot) account. You may specify individual subreddits, metasubs like r/all, or any other set of subreddits as described by the [praw docs](https://praw.readthedocs.io/en/latest/code_overview/models/subreddit.html). You may then simply call `sedbot --help` for more information.

There is a dry run mode which will not post any replies, and a mode to allow self replies for debugging purposes. I strongly advise against allowing self replies in production, as it is possible to create a regex which causes the bot to continuously reply to itself (e.g. ``s/(`+s\/.+\/`+)/`\1`/``).


## Installation

```console
pip install reddit-sedbot
```

## License

`reddit-sedbot` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
