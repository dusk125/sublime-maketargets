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

def plugin_unloaded():
   settings = Settings()
   settings.clear_on_change('show_last_cmd_status_bar')
   settings.clear_on_change('ignored_target_prefixes')

def Window(window=None):
   return window if window else sublime.active_window()

def Variables(window=None):
   return Window(window).extract_variables()

def Expand(variable, window=None):
   return sublime.expand_variables(variable, Variables(window))

def Settings(file='MakeTargets.sublime-settings'):
   return sublime.load_settings(file)

def RunCommand(command):
   cwd = Variables()['project_path']

   si = subprocess.STARTUPINFO()
   si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
   return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd=cwd, startupinfo=si)

def GetTargets(makefile=None):
   if not makefile:
      makefile = Expand('${project_path}/Makefile')

   targets = None
   if os.path.isfile(makefile):
      proccess = RunCommand('grep \'^[^#[:space:]].*:\' {}'.format(makefile))
      stdout, _ = proccess.communicate()

      targets = []
      for line in stdout.split('\n'):
         line = line.strip()
         if line and not any([line.startswith(ignore) for ignore in Settings().get('ignored_target_prefixes', [])]):
            targets.append(line.split(':')[0].strip())

   return targets

def PanelArg(variant='', caption='MakeTargets'):
   return dict(
      args=dict(
         build_system='Packages/User/MakeTargets.sublime-build',
         choice_build_system=True,
         choice_variant=True,
         variant=variant
      ),
      caption=caption,
      command='build'
   )

class MakeTargetsCommand(sublime_plugin.WindowCommand):
   def __init__(self, edit):
      sublime_plugin.WindowCommand.__init__(self, edit)
      self.build = Settings('MakeTargets.sublime-build')
      self._targets = None
      self.need_regen = True

      settings = Settings()
      settings.add_on_change('show_last_cmd_status_bar', self.on_show_last_change)
      settings.add_on_change('ignored_target_prefixes', self.on_ignore_prefixes_change)

   @property
   def targets(self):
      if not self._targets:
         self._targets = GetTargets()
      return self._targets

   def build_now(self, target, args={}):
      self.window.run_command('exec', dict(
         update_phantoms_only=True
      ))

      cmd = 'make {}'.format(target).strip()

      self.window.run_command('exec', dict(
         cmd=cmd,
         file_regex=args.get('file_regex', FILE_REGEX),
         syntax=args.get('syntax', SYNTAX),
         working_dir=args.get('working_dir', Expand(WORKING_DIR, self.window))
      ))

      settings = Settings()

      if settings.get('show_last_cmd_status_bar', False):
         value = settings.get('status_bar_format', '{command}')
         if '{command}' not in value:
            value += '{command}'
         self.window.active_view().set_status('mt_last_target', value.format(command=cmd))

   def show_panel(self):
      panel_args = {
         'items': [
            PanelArg(
               variant=target.get('name', ''),
               caption='MakeTargets - {}'.format(target.get('make_target', ''))
            )
            for target in self.build.get('variants')
         ]
      }
      panel_args['items'].insert(0, PanelArg())
      self.window.run_command('quick_panel', panel_args)

   def run(self, **args):
      if args.get('kill'):
         self.window.run_command('exec', dict(
            kill=True
         ))
         return

      if self.need_regen or (self.targets and not self.build.get('variants', None)):
         self.need_regen = False
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

   # override
   def on_show_last_change(self):
      if not Settings().get('show_last_cmd_status_bar', False):
         self.window.active_view().erase_status('mt_last_target')

   # override
   def on_ignore_prefixes_change(self):
      self._targets = None
      self.need_regen = True
