# Updates the release numbers of projects 

[![pipeline status](http://gitlab.ville.tg/fguerin/bump-release/badges/master/pipeline.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)

[![coverage report](http://gitlab.ville.tg/fguerin/bump-release/badges/master/coverage.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)


This script uses the release.ini file placed at the root of the project.


```ini
[DEFAULT]
current_release = 0.1.0  # Current version of the projects 

[main_project]
path = <project>/settings/base.py
pattern = r"^__version__\s*=\s*VERSION\s*=\s*['\"][.\d\w]+['\"]$" # Optional
template = '__version__ = VERSION = "{major}.{minor}.{release}"\n' # Optional

[node_module]
path = <project>/assets/package.json
key = "version"   # Optional

[sonar]
path = ./sonar-project.properties
pattern = r"^sonar.projectVersion=([.\d]+)$" # Optional
template = "sonar.projectVersion={major}.{minor}\n" # Optional

[docs]
path = <project>/../docs/source/conf.py
version_pattern = r"^version\s+=\s+[\"']([.\d]+)[\"']$" # Optional
version_format = 'version = "{major}.{minor}"\n' # Optional
release_pattern = r"^release\s+=\s+[\"']([.\d]+)[\"']$" # Optional
release_format = 'release = "{major}.{minor}.{release}"\n' # Optional

[ansible]
path = <project>/../ansible/prod/vars/vars.yml"
key = "git.version" # Optional

```
