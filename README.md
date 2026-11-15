# SeekDeploy Labs

The code, configs and run logs behind the hands-on articles on
[seekanddeploy.io](https://seekanddeploy.io).

When a SeekDeploy article says "I ran this", the evidence is here: every
command, the versions used, the output, and what broke along the way.

## Layout

One folder per article, named after the article's slug:

```
<article-slug>/
  README.md      what the build is, how to run it, link to the article
  RUN-LOG.md     dated log: environment, versions, commands, output, failures
  ...            the code and config used in the article
```

## Running a build

Each folder's README lists its requirements and exact commands. Builds are
written to run on a clean Linux machine; versions are pinned where it matters.
If something no longer works because a tool has moved on, open an issue and
say which version you tried.

## What the run logs are for

Each build keeps a run log, and failures stay in it. Wrong assumptions, error
messages, dead ends and the eventual fix are part of the record, because that's
the part you can't get from the docs.

Logs never contain real secrets. Any key or token you see is a deliberately fake
value.

## Bylines

Folders are written under SeekDeploy's house bylines (Wren Halloran, Idris
Okonjo, Petra Lindqvist, Tobias Brandt, Nadia Farouk and Sora Villanueva), each
covering a fixed beat. Every build is reviewed by the SeekDeploy editorial team
before it's merged here.

## Licence

MIT. See [LICENSE](LICENSE). Use anything here however you like.
