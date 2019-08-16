import os, sublime, sublime_plugin, subprocess, json, shutil

FILE_REGEX = '^(..[^:\n]*):([0-9]+):?([0-9]+)?:? (.*)'
SYNTAX = 'Packages/Makefile/Make Output.sublime-syntax'
WORKING_DIR = '${folder:${project_path:${file_path}}}'
CANNED = {
   'target': 'make_targets',
   'file_regex': FILE_REGEX,
   'working_dir': WORKING_DIR,
   'selector': 'source.makefile',
   'syntax': SYNTAX,
   'keyfiles': ['Makefile', 'makefile'],
   'cancel': {'kill': True},
   'variants': []
}

REMOVE_THIS = True

def plugin_loaded():
   build_file = 'MakeTargets.build-template'
   dest_file = '{}/User/MakeTargets.sublime-build'.format(sublime.packages_path())
   if REMOVE_THIS or not os.path.isfile(dest_file):
      with open(dest_file, 'w') as f:
         json.dump(CANNED, f, indent=2)

def Window(window=None):
   return window if window else sublime.active_window()

def Variables(window=None):
   return Window(window).extract_variables()

def Expand(variable, window=None):
   return sublime.expand_variables(variable, Variables(window))

def Settings():
   return sublime.load_settings('MakeTargets.sublime-settings')

def RunCommand(command):
   cwd = Variables()['project_path']

   si = subprocess.STARTUPINFO()
   si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
   return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd=cwd, startupinfo=si)

def GetTargets(makefile=None):
   if not makefile:
      makefile = Expand('${project_path}/Makefile')

   proccess = RunCommand('grep \'^[^#[:space:]].*:\' {}'.format(makefile))
   stdout, _ = proccess.communicate()

   targets = [line.split(':')[0].strip() for line in stdout.split('\n') if line.strip() and not (line.startswith('$') or line.startswith('.'))]
   return targets

class MakeTargetsCommand(sublime_plugin.WindowCommand):
   def __init__(self, edit):
      sublime_plugin.WindowCommand.__init__(self, edit)
      self.build = sublime.load_settings('MakeTargets.sublime-build')
      self._targets = None

   @property
   def targets(self):
      if not self._targets:
         self._targets = GetTargets()
      return self._targets

   def build_now(self, target, args={}):
      self.window.run_command('exec', dict(
         update_phantoms_only=True
      ))

      if 'make' in target:
         target.replace('make', '')

      self.window.run_command('exec', dict(
         cmd='make {}'.format(target),
         file_regex=args.get('file_regex', FILE_REGEX),
         syntax=args.get('syntax', SYNTAX),
         working_dir=args.get('working_dir', Expand(WORKING_DIR, self.window))
      ))

   def show_panel(self):
      panel_args = {
         'items': [
            dict(
               args=dict(
                  build_system='Packages/User/MakeTargets.sublime-build',
                  choice_build_system=True,
                  choice_variant=True,
                  variant=target.get('name', '')
               ),
               caption='MakeTargets - {}'.format(target.get('make_target', '')),
               command='build'
            )
            for target in self.build.get('variants')
         ]
      }
      panel_args['items'].insert(0,
         dict(
            args=dict(
               build_system='Packages/User/MakeTargets.sublime-build',
               choice_build_system=True,
               choice_variant=True,
               variant=''
            ),
            caption='MakeTargets',
            command='build'
         )
      )
      self.window.run_command('quick_panel', panel_args)

   def run(self, **args):
      if args.get('kill'):
         self.window.run_command('exec', dict(
            kill=True
         ))
         return

      if self.targets and not self.build.get('variants', None):
         self.build.set('variants', [dict(name=target, make_target=target) for target in self.targets])
         sublime.save_settings('MakeTargets.sublime-build')
         self.show_panel()
         return

      target = args.get('make_target', '')
      if target == '<<no target>>':
         target = ''
      self.build_now(target, args)

   def input(self, args):
      return self.MakeTarget()

   class MakeTarget(sublime_plugin.ListInputHandler):
      def list_items(self):
         targets = GetTargets()
         targets.insert(0, '<<no target>>')
         return targets
