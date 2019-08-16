# Make Targets
Make Targets was created to allow Sublime Text to run more than the 'Make' and 'Make Clean' Make targets. It does this by scanning a projects Makefile and figuring out the various targets, making them available as variants of the 'MakeTargets' build system.
## Installation
#### Git Clone
First, find out where the packages directory is by going to (Preferences->Browse Packages), use that location in the git clone command.
#### Package Control
Install from Package Control [coming soon]().
## Usage
Select 'MakeTargets' as your build system and start a build like normal.

Using the 'Build With' command (ctrl+shift+b by default), you can change the Make target that will run on subsequient 'Build' (ctrl+b) commands; MakeTargets will remember the last target you ran!

The 'MakeTargets' command is also available from the Command Palette.
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
* make_target

  The target to make, can be an empty string or None.
