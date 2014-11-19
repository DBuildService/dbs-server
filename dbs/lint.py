from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import git
import shutil
import subprocess
import tempfile
import os
import json

def html_escape(s):
    # In python3 we can use html.escape(s, quote=False)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class DockerfileLint:
    rules = "/usr/lib/node_modules/dockerfile_lint/sample_rules.yaml"

    PF_CLASSES = { 'error':
                   { 'alert': '<div class="alert alert-danger">',
                     'icon': """
  <span class="pficon-layered">
    <span class="pficon pficon-error-octagon"></span>
    <span class="pficon pficon-error-exclamation"></span>
  </span>""" },

                   'warn':
                   { 'alert': '<div class="alert alert-warning">',
                     'icon': """
  <span class="pficon-layered">
    <span class="pficon pficon-warning-triangle"></span>
    <span class="pficon pficon-warning-exclamation"></span>
  </span>""" },

                   'info':
                   { 'alert': '<div class="alert alert-info">',
                     'icon': """
  <span class="pficon pficon-info"></span>"""}
                   }

    def __init__ (self, git_url, git_path=None, git_commit=None):
        self._git_url = git_url
        self._git_path = git_path
        self._git_commit = git_commit
        self._temp_dir = None

    def __del__ (self):
        if self._temp_dir:
            try:
                shutil.rmtree(self._temp_dir)
            except (IOError, OSError, AttributeError) as exc:
                pass

    def _get_dockerfile (self):
        self._temp_dir = tempfile.mkdtemp ()
        git.Repo.clone_from (self._git_url, self._temp_dir)
        if self._git_path:
            if self._git_path.endswith('Dockerfile'):
                git_df_dir = os.path.dirname(self._git_path)
                df_path = os.path.abspath(os.path.join(self._temp_dir,
                                                       git_df_dir))
            else:
                df_path = os.path.abspath(os.path.join(self._temp_dir,
                                                       self._git_path))
        else:
            df_path = self._temp_dir

        self._Dockerfile = os.path.join(df_path, "Dockerfile")

    def _run_dockerfile_lint (self):
        with open ("/dev/null", "rw") as devnull:
            dfl = subprocess.Popen (["dockerfile_lint",
                                     "-j",
                                     "-r", self.rules,
                                     "-f", self._Dockerfile],
                                    stdin=devnull,
                                    stdout=subprocess.PIPE,
                                    stderr=devnull,
                                    close_fds=True)

        (stdout, stderr) = dfl.communicate ()
        jsonstr = stdout.decode ()
        self._lint = json.loads (jsonstr)

    def _mark_dockerfile (self):
        out = ""
        with open(self._Dockerfile, "r") as df:
            dflines = df.readlines ()
            dflines.append ("\n") # Extra line to bind 'absent' messages to
            lastline = len (dflines)
            msgs_by_linenum = {}
            for severity in ["error", "warn", "info"]:
                for msg in self._lint[severity]["data"]:
                    if "line" in msg:
                        linenum = msg["line"]
                    else:
                        linenum = lastline

                    msgs = msgs_by_linenum.get (linenum, [])
                    msgs.append (msg)
                    msgs_by_linenum[linenum] = msgs

            linenum = 1
            for line in dflines:
                msgs = msgs_by_linenum.get (linenum, [])
                linenum += 1
                if not msgs:
                    continue

                display_line = False
                msgout = ""
                for msg in msgs:
                    if "line" in msg:
                        display_line = True

                    level = msg["level"]
                    classes = self.PF_CLASSES.get (level)
                    if not classes:
                        continue

                    msgout += classes["alert"] + classes["icon"] + "\n"
                    msgout += ("  <strong>" +
                               html_escape (msg["message"]) +
                               "</strong> ")
                    description = msg.get ("description", "None")
                    if description != "None":
                        msgout += html_escape (description)
                    url = msg.get ("reference_url", "None")
                    if url != "None":
                        if type (url) == list:
                            url = reduce (lambda a, b: a + b, url)

                        msgout += (' <a href="%s\" class="alert-link">'
                                   '(more info)</a>' % url)
                    msgout += "\n</div>\n"

                if display_line:
                    out += (("<pre>%d:" % linenum) +
                            html_escape (line).rstrip () + "</pre>\n")

                out += msgout

        if out == "":
            out = """
<div class='alert alert-success'>
  <span class='pficon pficon-ok'></span>
  <strong>Looks good!</strong> This Dockerfile has no output from dockerfile_lint.
</div>
"""

        self._html_markup = out

    def run (self):
        self._get_dockerfile ()
        self._run_dockerfile_lint ()
        self._mark_dockerfile ()

        if self._temp_dir:
            try:
                shutil.rmtree(self._temp_dir)
                self._temp_dir = None
            except (IOError, OSError) as exc:
                pass

        return self._html_markup

    def get_json (self):
        return self._lint

if __name__ == "__main__":
    git_url = "https://github.com/TomasTomecek/docker-hello-world.git"
    lint = DockerfileLint (git_url)
    print (lint.run ())
