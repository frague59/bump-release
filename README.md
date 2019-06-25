# Updates the release numbers of projects 

[![pipeline status](http://gitlab.ville.tg/fguerin/bump-release/badges/master/pipeline.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)

[![coverage report](http://gitlab.ville.tg/fguerin/bump-release/badges/master/coverage.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)


This script uses the release.ini file placed at the root of the project.

```ini
[DEFAULT]
current_release = 0.1.0  # Current version of the projects 

[main_project]
path = <relative path the main>
# Can be a django settings or something else, with 
# `__version__ = VERSION = "<major>.<minor>.<release>"`

[node_module]
path = <relative path the package.json file>
# Can be any JSON file with a tag named `version`
 
[sonar]
path = <relative path the sonar-project.properties file>
# path = ./sonar-project.properties

[docs]
path = <relative path the sphinx configuration file>
# path = ./docs/source/conf.py

```
