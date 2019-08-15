import os, sublime, sublime_plugin, subprocess

def Window(window=None):
   return window if window else sublime.active_window()

def Variables(window=None):
   return Window(window).extract_variables()

def Expand(variable, window=None):
   return sublime.expand_variables(variable, Variables(window))

FILE_REGEX = '^(..[^:\n]*):([0-9]+):?([0-9]+)?:? (.*)'
SYNTAX = 'Packages/Makefile/Make Output.sublime-syntax'
WORKING_DIR = '${folder:${project_path:${file_path}}}'

def RunCommand(command):
   cwd = Variables()['project_path']

   si = subprocess.STARTUPINFO()
   si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
   return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd=cwd, startupinfo=si)

def GetTargets():
   proccess = RunCommand('grep \'^[^#[:space:]].*:\' {}'.format(Expand('${project_path}/Makefile')))
   stdout, _ = proccess.communicate()

   return [line.split(':')[0].strip() for line in stdout.split('\n') if line.strip() and not (line.startswith('$') or line.startswith('.'))]

class MakeTargetsCommand(sublime_plugin.WindowCommand):
   def __init__(self, edit):
      sublime_plugin.WindowCommand.__init__(self, edit)

   def build_now(self, targets_list, working_dir=None, file_regex=FILE_REGEX, syntax=SYNTAX):
      self.window.run_command('exec', dict(
         update_phantoms_only=True
      ))

      self.window.run_command('exec', dict(
         cmd='make {}'.format(targets_list),
         file_regex=file_regex,
         syntax=syntax,
         working_dir=working_dir if working_dir else Expand(WORKING_DIR, self.window)
      ))

   def on_done(self, index):
      if index > -1:
         target = GetTargets()[index]

         self.build_now(targets_list=target)

   def run(self, **args):
      if args.get('kill'):
         self.window.run_command('exec', dict(
            kill=True
         ))
         return

      if 'targets_list' in args:
         target = args['targets_list']
         self.build_now(target, *args)
      else:
         self.window.show_quick_panel(GetTargets(), self.on_done)

   def input(self, args):
      return self.TargetsList()

   class TargetsList(sublime_plugin.ListInputHandler):
      def list_items(self):
         return GetTargets()
