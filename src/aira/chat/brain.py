""" Load and save CSV, JSON, etc files containing Bot training data """
import traceback
import csv
import json
import random
from collections import Mapping

# import jinja2

from ..chat import constants
from .context import Context
from ..chat import pattern


def read_response_mapping(path=constants.DEFAULT_RESPONSE_MAPPING_PATH):
    with open(path, 'r') as fin:
        reader = csv.reader(fin)
        response_mapping = list(reader)
    return response_mapping


try:
    RESPONSE_MAPPING = pattern.PatternMap(read_response_mapping())
except IOError:
    print(traceback.format_exc())
    RESPONSE_MAPPING = pattern.PatternMap(constants.DEFAULT_RESPONSE_MAPPING)

try:
    ERROR_MESSAGES = pattern.PatternMap(read_response_mapping(constants.DEFAULT_ERROR_MESSAGES_PATH))
except IOError:
    # print("Can't find error messages in {}, so using defaults.".format(constants.DEFAULT_ERROR_MESSAGES_PATH))
    ERROR_MESSAGES = pattern.PatternMap(constants.DEFAULT_ERROR_MESSAGES)


def read_context(path=constants.DEFAULT_CONTEXT_PATH):
    context = constants.DEFAULT_CONTEXT
    try:
        with open(path) as fin:
            context = json.load(fin)
    except OSError:
        print(traceback.format_exc())
    return context


try:
    CONTEXT = Context(read_context())
except IOError:
    print(traceback.format_exc())
    CONTEXT = Context(constants.DEFAULT_CONTEXT)


def say(s):
    print(s)


class Responder:
    """ Uses a PatternMap and TemplateRenderer to respond to user statements (strings) """
    prefix_punc = r'@:-+~,:;!?.'

    def __init__(self, sayer=print, patternmap=RESPONSE_MAPPING, context=CONTEXT,
                 error_messages=ERROR_MESSAGES, ignore_prefix=constants.BOT_NAME):
        self.say = sayer
        # If your command line app is called "hey" and `ignore_prefix="Bot"` then
        #   the user can say "hey Bot, read this" and that's interpreted as "read this".
        self.ignore_prefix = ignore_prefix

        if isinstance(patternmap, list):
            self.patternmap = pattern.PatternMap(patternmap)
        elif isinstance(patternmap, Mapping):
            self.patternmap = pattern.PatternMap(list(zip(patternmap.keys(), patternmap.values())))
        else:
            self.patternmap = patternmap

        self.context = Context(context or CONTEXT)

        if isinstance(error_messages, list):
            self.error_messages = pattern.PatternMap(error_messages)
        elif isinstance(error_messages, Mapping):
            self.error_messages = pattern.PatternMap(list(zip(error_messages.keys(), error_messages.values())))
        else:
            self.error_messages = error_messages

    def interpolate_template(self, template, context_update=None):
        # FIXME: need `Context.recursive_update(nested_dict)`
        self.context.update(context_update if context_update is not None else {})
        return template.format(**self.context)

    def find_response_templates(self, statement):
        """ Find the possible response templates
        Args:
            statement (str): statement to respond to
        Returns:
            [str]: list of possible response templates

        >>> responder = Responder()
        >>> responder.find_response_templates('hi')[0]
        "Hi! I'm {bot_name}. How can I help you?"
        >>> responder.ignore_prefix = "Bot"
        >>> responder.find_response_templates('Bot hi')[0]
        "Hi! I'm {bot_name}. How can I help you?"
        """
        if statement.lower().lstrip().lstrip(self.prefix_punc).startswith(self.ignore_prefix):
            statement = statement.lstrip().lstrip(self.prefix_punc)[len(self.ignore_prefix):].lstrip(self.prefix_punc)
        return self.patternmap[statement]

    def find_response(self, statement, context_update=None):
        """ Find a response template and populate it with context vars, returning a response str

        Args:
            statement (str): statement to respond to
        Returns:
            str: populated template to be uttered by the chat bot

        >>> responder = Responder()
        >>> responder.find_response('hi Bot') in ['Hi! How can I help you.', 'Hi user, How can I help you?']
        True
        """
        templates = self.find_response_templates(statement)
        if templates is None or len(templates) < 1:
            templates = self.error_messages['unknown_command']
        return self.interpolate_template(
            template=templates[random.randint(0, len(templates) - 1)],
            context_update=context_update)

    def respond(self, statement, context_update=None):
        response = self.find_response(statement, context_update=context_update)
        if response is None:
            self.say("I don't understand.")
        else:
            self.say(response)
        return response


def normalize_statement(statement):
    return ' '.join(statement).strip().lower().replace("!", "").replace(".", "").replace(",", "").replace("?", "")


def respond(statement):
    """ Generating the response from the bot
    Args:
        args([int], [int]) : the probabilites of choosing choice A as the response or choice B as the response
    Returns:
        returns([str]) : The bot response

    >>> respond(['Hi Bot']) in ['Hi! How can I help you.', 'Hi user, How can I help you?']
    True
    """
    possible_responses = []
    patterns = list(RESPONSE_MAPPING.exact_strs.keys())
    templates = list(RESPONSE_MAPPING.exact_strs.values())
    for (patt, tmpl) in zip(patterns, templates):
        if (normalize_statement(statement) == normalize_statement(patt)):
            possible_responses = tmpl
            break
    if len(possible_responses):
        random_response_index = random.randint(0, len(possible_responses) - 1)
        Bot_response = possible_responses[random_response_index]
    else:
        Bot_response = None
    say(Bot_response or "I don't understand")
    return Bot_response