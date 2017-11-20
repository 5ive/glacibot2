""" Utility to dynamically load/reload modules during runtime """

import os
import importlib
import command
from env import GLOBAL

def load(name):
    """ Load a new module in and return it """

    try:
        return importlib.import_module(name)
    except Exception as exception:
        print("'{0}' error in {1}. Failed to load.".format(exception, name))

def refresh(module):
    """ Reload the specified module's code """

    try:
        importlib.reload(module)
        return True
    except Exception as exception:
        print("'{0}' error in {1}. Failed to refresh.".format(exception, module.__name__))
        return False

def scan():
    """ Scan for not-previously-loaded modules and load them """

    new_commands = []
    failed_commands = []

    for name in os.listdir('./commands/'):
        print('starting to look at {0}'.format(name))
        found_command = False

        if os.path.isdir('./commands/{0}'.format(name)):
            # attempt to load the module file
            module = load('commands.{0}.main'.format(name))

            # iterate through every object inside the module
            for attribute in module.__dict__:
                entry_name = attribute.lower()

                # make sure it isn't already loaded
                if entry_name not in GLOBAL['commands']:
                    try:
                        candidate = module.__dict__[attribute]

                        # is this a class that derives from Command?
                        if issubclass(candidate, command.Command) and entry_name not in GLOBAL['commands']:
                            # instantiate it and add it to the list of commands
                            GLOBAL['commands'][entry_name] = candidate()
                            new_commands.append(entry_name)

                            GLOBAL['commands'][entry_name].initialize()

                            print("loaded {0}".format(entry_name))
                            found_command = True

                    except TypeError:
                        continue

        if not found_command:
            failed_commands.append(name.lower())

    print('new: {0}'.format(new_commands))
    print('failed: {0}'.format(failed_commands))
