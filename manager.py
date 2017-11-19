""" Utility to dynamically load/reload modules during runtime """

import sys
import os
import importlib
from env import GLOBAL

def load(name):
    """ Load a new module in and return it """
    return importlib.import_module(name)

def refresh(module):
    """ Reload the specified module's code """

    try:
        importlib.reload(module)
        return True
    except:
        return False

def scan():
    """ Scan for not-previously-loaded modules and load them """

    new_commands = []
    failed_commands = []

    for name in os.listdir('./commands/'):
        # Make sure it's a directory, and we don't already have it loaded
        if os.path.isdir('./commands/{0}'.format(name)) and name not in GLOBAL['commands']:
            try:
                command = load('commands.{0}.main'.format(name))

                if 'run' in dir(command):
                    GLOBAL['commands'][name] = command
                    new_commands.append(name)
                else:
                    print("Couldn't find run(...) in {0}. Skipping command.".format(name))
                    failed_commands.append(name)

            except:
                # Get the 'compile' error, skip this command
                print("'{0}' error in {1}. Skipping command.".format(sys.exc_info()[1], name))
                failed_commands.append(name)

    return new_commands, failed_commands
