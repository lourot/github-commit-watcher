# gicowa.py - GitHub Commit Watcher

GitHub's *Watch* feature doesn't send notifications when commits are pushed. This script aims to
implement this feature and much more.

> **Under construction.** Basic features missing:
>
> * Remember last run's timestamp.
> * Line to be added to cron table.

## Installation

```
# sudo apt-get install sendmail
# sudo pip install PyGithub
$ git clone https://github.com/AurelienLourot/github-commit-watcher.git
```

Add the following line to your `.bashrc`:

```bash
alias gicowa='/path/to/github-commit-watcher/gicowa.py'
```

## Usage

### List repos watched by a user

```
$ gicowa watchlist AurelienLourot
AurelienLourot/uncommitted
AurelienLourot/crouton-emacs-conf
brillout/FasterWeb
AurelienLourot/github-commit-watcher
```

### List last commits on a repo

```
$ gicowa lastrepocommits AurelienLourot/github-commit-watcher 2015 07 05 09 12 00
2015-07-05 10:46:27 - Aurelien Lourot - Minor cleanup.
2015-07-05 09:39:01 - Aurelien Lourot - watchlist command implemented.
2015-07-05 09:12:00 - Aurelien Lourot - argparse added.
```

### List last commits on repos watched by a user

```
$ gicowa lastwatchedcommits AurelienLourot 2015 07 04 00 00 00
AurelienLourot/crouton-emacs-conf - 2015-07-04 17:08:48 - Aurelien Lourot - Support for Del key.
brillout/FasterWeb - 2015-07-04 16:38:55 - brillout - add README
AurelienLourot/github-commit-watcher - 2015-07-05 10:46:27 - Aurelien Lourot - Minor cleanup.
AurelienLourot/github-commit-watcher - 2015-07-05 09:39:01 - Aurelien Lourot - watchlist command implemented.
AurelienLourot/github-commit-watcher - 2015-07-05 09:12:00 - Aurelien Lourot - argparse added.
AurelienLourot/github-commit-watcher - 2015-07-05 09:07:14 - AurelienLourot - Initial commit
```

### Send output by e-mail

You can send the output of any command to yourself by e-mail:

```
$ gicowa --no-color --mailto myself@mydomain.com lastwatchedcommits AurelienLourot 2015 07 04 00 00 00
AurelienLourot/crouton-emacs-conf - 2015-07-04 17:08:48 - Aurelien Lourot - Support for Del key.
brillout/FasterWeb - 2015-07-04 16:38:55 - brillout - add README
AurelienLourot/github-commit-watcher - 2015-07-05 10:46:27 - Aurelien Lourot - Minor cleanup.
AurelienLourot/github-commit-watcher - 2015-07-05 09:39:01 - Aurelien Lourot - watchlist command implemented.
AurelienLourot/github-commit-watcher - 2015-07-05 09:12:00 - Aurelien Lourot - argparse added.
AurelienLourot/github-commit-watcher - 2015-07-05 09:07:14 - AurelienLourot - Initial commit
Sent by e-mail to myself@mydomain.com
```

> **NOTES:**
>
> * You probably want to use `--no-color` because your e-mail client is likely not to render the
>   bash color escape sequences properly.
> * The e-mails are likely to be considered as spam until you mark one as non-spam in your e-mail
>   client.

## Initial Author

[Aurelien Lourot](http://lourot.com/)
