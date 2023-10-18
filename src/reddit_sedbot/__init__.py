# SPDX-FileCopyrightText: 2023-present
#
# SPDX-License-Identifier: MIT
# This script will check reddit comments and run sed commands found against the parent comment or post

import logging
import shutil
import subprocess
from enum import Enum
from typing import Annotated

import marko
import praw
import typer

logging.basicConfig()
log = logging.getLogger("sedbot")
log.setLevel(logging.INFO)


class RunMode(str, Enum):
    DryRun = "DryRun"
    Live = "Live"


def _find_codeblocks(element: marko.inline.InlineElement | marko.block.BlockElement) -> list[marko.inline.CodeSpan]:
    # recursively find all codeblocks and codespans in a comment body
    codeblocks_and_codespans = []
    for child in element.children:
        if isinstance(child, marko.inline.CodeSpan):
            codeblocks_and_codespans.append(child)
        elif isinstance(child, (marko.inline.InlineElement, marko.block.BlockElement)):
            codeblocks_and_codespans.extend(_find_codeblocks(child))
    return codeblocks_and_codespans


def parse_sed_commands(comment_body: str) -> list[str]:
    # find sed commands in a line encolosed by matched sequences of '`'s
    # e.g. ``s/foo`/bar`` -> s/foo`/bar
    codeblocks = [
        elem.children for elem in _find_codeblocks(marko.parse(comment_body)) if isinstance(elem.children, str)
    ]
    if codeblocks:
        log.info("Found codeblocks: %s", codeblocks)
    return [elem for elem in codeblocks if elem.startswith("s/")]


def execute_sed_command(sed_command: str, pattern: str, input_str: str) -> str | None:
    # run a sed command with input
    # evil self modifying sed command
    # ``s/(`+s\/.+\/`+)/`\1`/`` in reply to a comment with exactly the same contents
    # will iteratively add one additional set of `` to the sed command
    # not actually a problem because in prod we don't allow self replies
    # but fun to think about
    try:
        return subprocess.check_output(
            [sed_command, "-re", pattern],  # noqa: S603
            input=input_str,
            text=True,
            stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        log.warning("sed command failed: %s", e.stderr)
        return None


def main(run_mode: Annotated[RunMode, typer.Option(case_sensitive=False)] = RunMode.DryRun,
         target_subreddit: str = "all",
         *,
         allow_self_reply: bool = False) -> None:
    # implements the same logic as above but without classes
    log.info("Starting sedbot in %s mode and subreddit '%s'", run_mode, target_subreddit)
    reddit = praw.Reddit("sedbot")
    subreddit = reddit.subreddit(target_subreddit)
    sed_command = shutil.which("sed")
    assert sed_command is not None  # noqa: S101
    for comment in subreddit.stream.comments(skip_existing=True):
        log.debug(f"processing: {comment}")
        if comment.author == reddit.user.me() and not allow_self_reply:
            log.info("Ignoring self reply")
            continue
        if isinstance(comment.parent(), praw.models.Submission):
            # ignore root comments for now
            continue
        result = comment.parent().body
        seds = parse_sed_commands(comment.body)
        if not seds:
            continue
        for sed_pattern in seds:
            log.info("Found sed command: %s", sed_pattern)
            result = execute_sed_command(sed_command, sed_pattern, input_str=result)
            if result is None:
                break
        if result is None:
            continue
        if result.strip() == comment.parent().body:
            log.info("Result is the same as the original comment, skipping")
            continue
        comment.refresh()
        if any(reply.author == reddit.user.me() for reply in comment.replies):
            log.info("Already replied to this comment, skipping")
            continue
        result = f"""\
{result}

---
I am a bot, and this action was performed automatically. Please contact [my creator](https://www.reddit.com/message/compose/?to=/u/thirdegree) if you have any questions.
""" # noqa: E501
        log.info("Result: %s", result)
        if run_mode is RunMode.Live:
            comment.reply(result)


def entry_point() -> None:
    typer.run(main)


if __name__ == "__main__":
    main()
