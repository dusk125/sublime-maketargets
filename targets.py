import os, sublime, sublime_plugin, subprocess, json, re

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
   'variants': [],
   'makefile': None
}
TARGET_REGEX = '(.+)\s*:\s{1}'

def plugin_loaded():
   build_file = 'MakeTargets.build-template'
   dest_file = '{}/User/MakeTargets.sublime-build'.format(sublime.packages_path())
   if not os.path.isfile(dest_file):
      with open(dest_file, 'w') as f:
         json.dump(CANNED, f, indent=2)

def plugin_unloaded():
   settings = Settings()
   settings.clear_on_change('show_last_cmd_status_bar')
   settings.clear_on_change('ignored_target_prefixes')
   settings.clear_on_change('target_regex')

def Window(window=None):
   return window if window else sublime.active_window()

def Variables(window=None):
   return Window(window).extract_variables()

def Expand(variable, window=None):
   return sublime.expand_variables(variable, Variables(window))

def Settings(file='MakeTargets.sublime-settings'):
   return sublime.load_settings(file)

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
      settings = Settings()
      settings.add_on_change('show_last_cmd_status_bar', self.on_show_last_change)
      settings.add_on_change('ignored_target_prefixes', self.on_ignore_prefixes_change)
      settings.add_on_change('target_regex', self.on_target_regex_change)

      self.build = Settings('MakeTargets.sublime-build')
      self._targets = None
      self.need_regen = True
      self.target_regex = re.compile(settings.get('target_regex', TARGET_REGEX))

   @property
   def makefile(self):
      return os.path.join(Expand('${project_path}', self.window), 'Makefile')

   @property
   def targets(self):
      if not self._targets:
         targets = []

         if os.path.isfile(self.makefile):
            with open(self.makefile, 'r') as f:
               for line in f.readlines():
                  if self.target_regex.search(line):
                     line = line.strip()
                     if line and not any([line.startswith(ignore) for ignore in Settings().get('ignored_target_prefixes', [])]):
                        targets.append(line.split(':')[0].strip())

         self._targets = targets
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

   def regen_targets(self):
      self.need_regen = False
      self._targets = None
      self.build.set('makefile', self.makefile)
      self.build.set('variants', [dict(name=target, make_target=target) for target in self.targets])
      sublime.save_settings('MakeTargets.sublime-build')

   def run(self, **args):
      if args.get('kill'):
         self.window.run_command('exec', dict(
            kill=True
         ))
         return

      if args.get('regen', False):
         self.regen_targets()
         return

      if self.need_regen or (self.targets and not self.build.get('variants', None) or (self.makefile != self.build.get('makefile', None))):
         self.regen_targets()
         self.show_panel()
         return

      if args.get('palette', False):
         self.show_panel()
         return

      target = args.get('make_target', '')
      if target == '<<no target>>':
         target = ''

      self.build_now(target, args)

   # override
   def on_show_last_change(self):
      if not Settings().get('show_last_cmd_status_bar', False):
         self.window.active_view().erase_status('mt_last_target')

   # override
   def on_ignore_prefixes_change(self):
      self._targets = None
      self.need_regen = True

   # override
   def on_target_regex_change(self):
      self.target_regex = re.compile(Settings().get('target_regex', TARGET_REGEX))
