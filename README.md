# Updates the release numbers for a projects

This script uses the release.ini file placed at the root of the project, and replaces the version or release number in various files.

```sh
$ cd <project_root>
$ ls -al
...
release.ini
...
$ bump_release <major>.<minor>.<release>
```

## Installation

On linux, the best place to install it is for the user:

```sh
$ pip install --user bump-release
```

Assume to have `~/.local/bin` in the `$PATH`.

## Version numbers that can be updated

+ main project version
+ node package.json
+ sonar properties
+ sphinx docs
+ ansible variables in a vars file
+ setup.py

## release.ini

The .ini file provides path, patterns and templates to update files.

If a section is not present, no action if performed for this section.

The application provides some "standard" patterns and templates (aka. the ones I use in my projects). If you provide some patterns and templates, you have to enclose them with double-quotes. Due to [configparser](https://docs.python.org/3/library/configparser.html) limitations, all strings are parsed as raw strings.

The application removes those double-quotes through a :
```python
pattern = config["<section>"].get("pattern") or DEFAULT_PATTERN
pattern = pattern.strip('"')
```

### Exemple ini file:

```ini
[DEFAULT]
current_release = 0.1.0  # Current version of the projects, will be updated by the script

[main_project]
path = <project>/settings/base.py
# Optional pattern, default is...
pattern = "^__version__\s*=\s*VERSION\s*=\s*['\"][.\d\w]+['\"]$"
# Optional template, default is...
template = "__version__ = VERSION = '{major}.{minor}.{release}'"

[node_module]
path = <project>/assets/package.json
# Optional key, default is...
key = "version"

[sonar]
path = ./sonar-project.properties
# Optional pattern, default is...
pattern = "^sonar.projectVersion=([.\d]+)$"
# Optional template, default is...
template = "sonar.projectVersion={major}.{minor}"

[docs]
path = <project>/../docs/source/conf.py
# Optional pattern, default is...
version_pattern = "^version\s+=\s+[\"']([.\d]+)[\"']$"
# Optional template, default is...
version_format = "version = '{major}.{minor}'"
# Optional pattern, default is...
release_pattern = "^release\s+=\s+[\"']([.\d]+)[\"']$"
# Optional template, default is...
release_format = "release = '{major}.{minor}.{release}'"

[ansible]
path = <project>/../ansible/prod/vars/vars.yml"
# Optional key - The script searches for the "git" root key, and then for "version" sub-key
key = "git.version"

[setup]
path = <project>/setup.py
# Optional pattern, default is...
pattern = "^\s*version=['\"]([.\d]+)['\"],$"
# Optional template, default is...
template = "    version='{major}.{minor}.{release}',"
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
