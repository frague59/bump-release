# Updates the release numbers of projects 

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
