from setuptools import setup
import gicowa

setup(name="gicowa",
      version=gicowa.__version__,
      install_requires=["PyGithub"],
      description="GitHub Commit Watcher",
      long_description=open("README").read(),
      keywords=["gicowa",
                "github",
                "commit",
                "commits",
                "watcher",
                "watch",
                "push",
                "pushed",
                "notification",
                "notifications"],
      author="Aurelien Lourot",
      author_email="aurelien.lourot@gmail.com",
      url="https://github.com/AurelienLourot/github-commit-watcher",
      download_url="https://github.com/AurelienLourot/github-commit-watcher/tarball/"
                   + gicowa.__version__,
      license="public domain",
      classifiers=["Development Status :: 4 - Beta",
                   "Environment :: Console",
                   "Intended Audience :: Developers",
                   "License :: Public Domain",
                   "Natural Language :: English",
                   "Operating System :: POSIX :: Linux",
                   "Programming Language :: Python :: 2.7",
                   "Topic :: Software Development :: Version Control",
                   "Topic :: Utilities"],
      packages=["gicowa",
                "gicowa/impl"],
      entry_points="""
[console_scripts]
gicowa = gicowa.gicowa:main
""")
