# Release a new version

## Increase the version number

In [gicowa/\__init\__.py](gicowa/__init__.py) to `7.8.9` in this example.

## Extend the changelog

In [README.html](README.html)

## Generate the documentation in other formats

```
$ sudo pip install -r requirements.txt
$ sudo apt-get install pandoc
$ ./scripts/gen_doc.sh
```

## Generate the package to be published

```
$ python setup.py sdist
```

And check that the resulting `dist/gicowa-7.8.9.tar.gz` looks well-formed.

## Install the package locally

```
$ sudo apt-get install sendmail
$ sudo pip install dist/gicowa-7.8.9.tar.gz
```

and test it briefly, e.g.

```
$ gicowa watchlist AurelienLourot
```

## Commit your changes, create a git tag and push

```
$ git add -u
$ git commit -m "Version 7.8.9"
$ git push
$ git tag "7.8.9"
$ git push --tags
```

## Push the package to PyPI Test

Create `~/.pypirc` as follows:

```
[distutils]
index-servers =
    pypi
    pypitest

[pypi]
repository: https://pypi.python.org/pypi
username:lourot
password:mypassword

[pypitest]
repository: https://testpypi.python.org/pypi
username:lourot
password:mypassword
```

and push:

```
$ python setup.py sdist upload -r pypitest
```

> **NOTE:** if this fails because the project doesn't exist in PyPI Test anymore, register it again:
>
> ```
> $ python setup.py register -r pypitest
> ```

Finally check that the package looks well-formed at `https://testpypi.python.org/pypi/gicowa/7.8.9`

## Push the package to PyPI

```
$ python setup.py sdist upload -r pypi
```

and check that the package looks well-formed at `https://pypi.python.org/pypi/gicowa/7.8.9`

Finally check that the package can be installed from PyPI:

```
$ sudo pip uninstall gicowa
$ sudo pip install gicowa
```

## Add release notes

to [https://github.com/AurelienLourot/github-commit-watcher/tags](https://github.com/AurelienLourot/github-commit-watcher/tags)
