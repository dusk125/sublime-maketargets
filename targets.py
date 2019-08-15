import os, sublime, sublime_plugin, subprocess, json, shutil

FILE_REGEX = '^(..[^:\n]*):([0-9]+):?([0-9]+)?:? (.*)'
SYNTAX = 'Packages/Makefile/Make Output.sublime-syntax'
WORKING_DIR = '${folder:${project_path:${file_path}}}'
CANNED = {
   'target': 'make_targets',
   'is_build_sys': True,
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
      self.last_target = None
      self.targets = None

   def build_now(self, targets_list, args={}):
      print('building', targets_list, args)
      self.window.run_command('exec', dict(
         update_phantoms_only=True
      ))

      if not targets_list.startswith('make'):
         targets_list = 'make {}'.format(targets_list)

      self.window.run_command('exec', dict(
         cmd=targets_list,
         file_regex=args.get('file_regex', FILE_REGEX),
         syntax=args.get('syntax', SYNTAX),
         working_dir=args.get('working_dir', Expand(WORKING_DIR, self.window))
      ))
      self.last_target = targets_list

   def on_done(self, index):
      if index > -1:
         target = self.targets[index].replace('MakeTargets', '').replace('|', '').strip()

         self.build_now(targets_list=target)

   def show_panel(self):
      self.targets = ['MakeTargets | {}'.format(target) for target in self.targets]
      self.targets.insert(0, 'MakeTargets')
      self.window.show_quick_panel(self.targets, self.on_done)

   def run(self, **args):
      print('command', args)
      if args.get('kill'):
         self.window.run_command('exec', dict(
            kill=True
         ))
         return

      if not args.get('is_build_sys', False) and not self.build.get('variants', None):
         self.targets = GetTargets()
         self.build.set('variants', [dict(name=target, new_target=target) for target in self.targets])
         sublime.save_settings('MakeTargets.sublime-build')

      if 'new_target' in args or self.last_target:
         target = args.get('new_target', self.last_target)
      else:
         self.show_panel()
         return

      self.build_now(target, args)

   def input(self, args):
      return self.NewTarget()

   class NewTarget(sublime_plugin.ListInputHandler):
      def list_items(self):
         return GetTargets()
