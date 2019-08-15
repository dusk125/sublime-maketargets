# Make Targets
Make Targets was created because I wanted to be able to easily execute any of the targets in my Makefile.
Make Targets automatically reads the Makefile in your project and tries to figure out what pieces are targets that you care about.
## Installation
#### Git Clone
First, find out where the packages directory is by going to (Preferences->Browse Packages), use that location in the git clone command.
#### Package Control
Install from Package Control [coming soon]().
## Usage
Select 'MakeTargets' as your build system and start a build!
#### Available Commands
`{'command': 'make_targets', 'args': see below}`
#### Available Arguments
All arguments are optional and have reasonable defaults.

* working_dir

  Where to build from.
  
  Defaults to the expansion of `'${folder:${project_path:${file_path}}}'`.
* file_regex

  The regex the build system looks for errors.
  
  Defaults to `'^(..[^:\n]*):([0-9]+):?([0-9]+)?:? (.*)'`.
* syntax

  The syntax to use for the output panel.
  
  Defaults to `'Packages/Makefile/Make Output.sublime-syntax'`.
