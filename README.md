# Updates the release numbers for a projects

[![pipeline status](http://gitlab.ville.tg/fguerin/bump-release/badges/master/pipeline.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)

[![coverage report](http://gitlab.ville.tg/fguerin/bump-release/badges/master/coverage.svg)](http://gitlab.ville.tg/fguerin/bump-release/commits/master)

This script uses the release.ini file placed at the root of the project.

## release.ini

```ini
[DEFAULT]
current_release = 0.1.0  # Current version of the projects

[main_project]
path = <project>/settings/base.py
# Optional pattern, default is...
pattern = r"^__version__\s*=\s*VERSION\s*=\s*['\"][.\d\w]+['\"]$"
# Optional template, default is...
template = '__version__ = VERSION = "{major}.{minor}.{release}"\n'

[node_module]
path = <project>/assets/package.json
# Optional key, default is...
key = "version"

[sonar]
path = ./sonar-project.properties
# Optional pattern, default is...
pattern = r"^sonar.projectVersion=([.\d]+)$"
# Optional template, default is...
template = "sonar.projectVersion={major}.{minor}\n"

[docs]
path = <project>/../docs/source/conf.py
# Optional pattern, default is...
version_pattern = r"^version\s+=\s+[\"']([.\d]+)[\"']$"
# Optional template, default is...
version_format = 'version = "{major}.{minor}"\n'
# Optional pattern, default is...
release_pattern = r"^release\s+=\s+[\"']([.\d]+)[\"']$"
# Optional template, default is...
release_format = 'release = "{major}.{minor}.{release}"\n'

[ansible]
path = <project>/../ansible/prod/vars/vars.yml"
# Optional key - The script searches for the "git" root key, and then for "version" sub-key
key = "git.version"

[setup]
path = <project>/setup.py
# Optional pattern, default is...
pattern = "^\s*version=['\"]([.\d]+)['\"],$"
# Optional template, default is...
template = "    version=\"{major}.{minor}.{release}\","

```

## Version numbers that can be updated

+ main project version
+ node package.json
+ sonar properties
+ sphinx docs
+ ansible variables in a vars file
+ setup.py

## Installation

```bash
$ pip install --user bump-release
```

## Usage

```bash
$ cd <project_root>
$ cat release.ini
[DEFAULT}
current_release = 0.0.1

[main_project]
path = "foo/__init__.py"

[sonar]
path = "sonar-project.properties"
...
$ cat foo/__init__.py
...
__version__ = VERSION = "0.0.1"
...
$ bump_release 0.0.2
...
$ cat release.ini
[DEFAULT}
current_release = 0.0.2
...
$ cat foo/__init__.py
...
__version__ = VERSION = "0.0.2"
...

```
