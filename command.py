""" Defines an abstract base class for custom commands """

import abc

class Command(abc.ABC):
    """ Abstract base class for custom commands """

    @abc.abstractmethod
    def initialize(self):
        """ Called directly after the command has been loaded """
        pass

    @abc.abstractmethod
    def destroy(self):
        """ Called when the command is about to be unloaded """
        pass

    @abc.abstractmethod
    async def command(self, message):
        """ Slack instance will pass events to this method for parsing """
        pass
