import sys, os, importlib

class Manager:
    def __init__(self):
        self.commands = {}

    def Load(self, name):
        return importlib.import_module(name)

    def Refresh(self, module):
        importlib.reload(module)

    def Rescan(self):
        # Right now this clobbers existing modules
        # This would mess up any stateful commands

        for name in os.listdir('./commands/'):
            if os.path.isdir('./commands/{0}'.format(name)):
                try:
                    command = self.Load('commands.{0}.main'.format(name))

                    if 'run' in dir(command):
                        self.commands[name] = command
                    else:
                        print("Couldn't find run(...) in {0}. Skipping command.".format(name))
                except:
                    error, tb = sys.exec_info()[1:]

                    print("'{0}' error in {1}, line {2}. Skipping command.".format(
                        error,
                        tb.tb_frame.f_code.co_filename,
                        tb.tb_lineno
                    ))

        print("Loaded commands: {0}".format(",".join(self.commands.keys())))

    def GetCommandList(self):
        return self.commands.values()
