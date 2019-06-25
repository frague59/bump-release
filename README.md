# Updates the release numbers of projects 

[![pipeline status](http://gitlab.ville.tg/fguerin/bump-release/badges/master/pipeline.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)

[![coverage report](http://gitlab.ville.tg/fguerin/bump-release/badges/master/coverage.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)


This script uses the release.ini file placed at the root of the project.

```ini
[DEFAULT]
current_release = 0.1.0  # Current version of the projects 

[main_project]
path = <relative path the main>

[node_module]
path = <relative path the package.json file>

[sonar]
path = <relative path the sonar-project.properties file>

[docs]
path = <relative path the sphinx configuration file>

```
