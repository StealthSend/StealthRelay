#! /usr/bin/env python

import os
import sys
import platform
import glob
import subprocess
import smtplib
import re
import Tkinter

from ConfigParser import SafeConfigParser

from string import printable

class StealthRelayError(Exception):
  pass

class ConfigError(StealthRelayError):
  pass


class FakeSecHead(object):
  """
  Alex Martelli: http://stackoverflow.com/a/2819788
  """
  def __init__(self, fp):
    self.fp = fp
    self.sechead = '[asection]\n'
  def readline(self):
    if self.sechead:
      try: return self.sechead
      finally: self.sechead = None
    else: return self.fp.readline()


def get_home_dir():
    """
    Returns the home directory of the account under which
    the python program is executed. The home directory
    is represented in a manner that is comprehensible
    by the host operating system (e.g. ``C:\\something\\``
    for Windows, etc.).
    
    Adapted directly from K. S. Sreeram's approach, message
    393819 on c.l.python (7/18/2006). I treat this code
    as public domain.
    """
    def valid(path) :
        if path and os.path.isdir(path) :
            return True
        return False
    def env(name) :
        return os.environ.get( name, '' )
    if sys.platform != 'win32' :
      homeDir = os.path.expanduser( '~' )
      if valid(homeDir):
        return homeDir
    homeDir = env( 'USERPROFILE' )
    if valid(homeDir) :
      return homeDir
    homeDir = env( 'HOME' )
    if valid(homeDir) :
      return homeDir   
    homeDir = '%s%s' % (env('HOMEDRIVE'),env('HOMEPATH'))
    if valid(homeDir) :
      return homeDir
    homeDir = env( 'SYSTEMDRIVE' )
    if homeDir and (not homeDir.endswith('\\')) :
      homeDir += '\\'
      if valid(homeDir) :
        return homeDir
    homeDir = 'C:\\'
    return homeDir


def read_config(config_file):
  """
  Returns the contents of a sectionless `config_file` as a `dict`.
  """
  cp = SafeConfigParser()
  cp.readfp(FakeSecHead(open(config_file)))
  return dict(cp.items('asection'))

def get_profiles(home):
  profiles = None
  if sys.platform == "darwin":
    profiles = os.path.join(home, "Library",
                                  "Thunderbird",
                                  "Profiles") 
  elif sys.platform.startswith("linux"):
    profiles = os.path.join(home, ".thunderbird")
  elif sys.platform == "win32":
    v = int(platform.version().split('.', 1)[0])
    if platform.release in (4, 5):
      profiles = os.path.join(home, "Application Data",
                                    "Thunderbird",
                                    "Profiles")
    elif platform.release >= 6:
      profiles = os.path.join(home, "AppData", "Roaming",
                                               "Thunderbird",
                                               "Profiles")
  return profiles

def main():
  home = get_home_dir()
  config_file = os.path.join(home, ".stealthrelay")
  if os.path.exists(config_file):
    config = read_config(config_file)
  else:
    raise ConfigError("Unable to find '%s' config." % config_file)
  if "mail" in config:
    profiles = config['mail']
  else:
    profiles = get_profiles(home)
  if profiles == None:
    raise ConfigError("Unable to find thunderbird profile.")
  debug = config.get("debug", False)
  if debug:
    tk = Tkinter.Tk()
    tk.title("StealthRelay")
    txt = Tkinter.Text(tk)
    txt.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
  stealthcoind = config['daemon']
  pattern = os.path.join(profiles, "*.default")
  default = glob.glob(pattern)[0]
  stealthtext = os.path.join(default, "Mail",
                             "Local Folders", "StealthRelay")
  client_id = config['client_id']
  rgx = '(%s,[A-Za-z0-9+/]+=*)(?:[^A-Za-z0-9+/=]|$)' % client_id
  clientRE = re.compile(rgx)

  lines = iter(open(stealthtext).read().splitlines()[::-1])

  subject = []
  for line in lines:
    line = "".join([c for c in line if c in printable])
    line = line.replace(" ", "+")
    line = line.split()
    line = "".join(line)
    subject.append(line.strip())
    if client_id in line:
      break
  subject = "".join(subject[::-1])
  # clientRE = re.compile('%s,[A-Za-z0-9+/=]+([^A-Za-z0-9+/=]|$)' % client_id)
  # print "----- subject -----"
  # print subject
  # print "----- subject -----"

  m = clientRE.search(subject)
  if m is None:
    if debug:
      txt.insert(Tkinter.END, "Could not find StealthText message.\n")
    msg = "<<Parse Error>>"
    # print subject
    raise SystemExit
    
  else:
    msg = m.group(1)
    if debug:
      txt.insert(Tkinter.END, msg)
  # lines = iter(open(stealthtext).read().splitlines()[::-1])
  # for line in lines:
  #   line = line.strip()
  #   if line:
  #     break
  # msg = lines.next().strip() + line
  command = [stealthcoind, "decryptsend", "%s" % (msg,)]
  # print "command is:"
  # print command
  output = subprocess.check_output(command)
  if debug:
    txt.insert(Tkinter.END, "\n\n" + output.strip())
  # output = "test\n"
  sys.stderr.write(output)
  if "confirm_address" in config:
    if output.startswith('<<'):
      message = config.get("fail", "-") + "\n"
    else:
      message = config.get("success", "+") + "\n"
    if "sender" in config:
      sender = config['sender']
    else:
      raise ConfigError("Setting 'email' not in config.")
    if "confirm_address" in config:
      receivers = [config['confirm_address']]
    else:
      raise ConfigError("Setting 'confirm_address' not in config.")
  else:
    message = "<No Message>"
    sender = "<No Sender>"
    receivers = []
  if "confirm_address" in config:
    try:
      server = smtplib.SMTP(config['server'])
      server.starttls()
      server.login(config['username'], config['password'])
      server.sendmail(sender, receivers, message)
      if debug:
        txt.insert(Tkinter.END, "\n\n" + "Email sent successfully.")
      else:
        sys.stderr.write("Email sent successfully.\n")
    except smtplib.SMTPException:
      if debug:
        txt.insert(Tkinter.END, "\n\n" + "Email unsuccessful.")
      else:
        sys.stderr.write("Email unsuccessful.\n")
  if debug:
    tk.mainloop()
    

if __name__ == "__main__":
  main()
