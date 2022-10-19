"""
Interface to argparse
"""
import argparse
import logging


class ParseArgs:  # pylint: disable=too-few-public-methods
    """
    Ingest list of dicts to construct command line switches and parse runtime directives
    """

    def __init__(self, name: str, description: str, argument_map: list) -> None:
        self.logger = logging.getLogger(__name__)
        self.name = name
        self.description = description
        self.argument_map = argument_map
        self.parse_args()

    def add_args(self, argument, group=None, exclusive_group=None):
        """
        Add arguments to parser, group or exclusive group
        """
        if group:
            self.logger.debug(group)
            if group not in self.command_group:
                self.command_group[group] = self.parser.add_argument_group()
            parser = self.command_group[group]
        elif exclusive_group:
            self.logger.debug(exclusive_group)
            if exclusive_group not in self.command_group:
                self.command_group[
                    exclusive_group
                ] = self.parser.add_mutually_exclusive_group(required=True)
            parser = self.command_group[exclusive_group]
        else:
            parser = self.parser

        self.logger.debug(parser)

        arg_map = {}
        arg_name = argument.get("switch")

        if "type" in argument:
            arg_map["type"] = argument["type"]
        if "default" in argument:
            arg_map["default"] = argument["default"]
        if "help" in argument:
            arg_map["help"] = argument["help"]
        if "required" in argument:
            arg_map["required"] = argument["required"]
        if "choices" in argument:
            arg_map["choices"] = argument["choices"]

        arg_map["action"] = argument.get("action", "store")

        self.logger.debug(arg_map)
        parser.add_argument(arg_name, **arg_map)

    def parse_args(self) -> None:
        """Parse args and return collection"""
        self.parser = argparse.ArgumentParser(description=self.description)
        self.command_group = {}
        for argument in self.argument_map:
            group = argument.get("group", False)
            exclusive_group = argument.get("exclusive_group", False)
            if group:
                self.add_args(argument, group=group)
            elif exclusive_group:
                self.add_args(argument, exclusive_group=exclusive_group)
            else:
                self.add_args(argument)

        self.args_parsed = self.parser.parse_args()
        self.logger.debug(self.args_parsed)
