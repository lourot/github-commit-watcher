# gicowa.py - GitHub Commit Watcher

> **NOT WORKING YET.** First version in construction.

GitHub's *Watch* feature doesn't send notifications when commits are pushed. This script aims to
implement this feature and much more.

```
# sudo pip install PyGithub

$ ./gicowa.py watchlist AurelienLourot
AurelienLourot/uncommitted
AurelienLourot/crouton-emacs-conf
brillout/FasterWeb
AurelienLourot/github-commit-watcher

$ ./gicowa.py lastrepocommits AurelienLourot/github-commit-watcher 2015 07 05 09 12 00
2015-07-05 10:46:27 - Aurelien Lourot - Minor cleanup.
2015-07-05 09:39:01 - Aurelien Lourot - watchlist command implemented.
2015-07-05 09:12:00 - Aurelien Lourot - argparse added.
```
