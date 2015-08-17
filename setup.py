from setuptools import setup
import gicowa

setup(name="gicowa",
      version=gicowa.__version__,
      description="GitHub Commit Watcher",
      long_description=open("README").read(),
      author="Aurelien Lourot",
      author_email="aurelien.lourot@gmail.com",
      url="http://lourot.com/gicowa",
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
