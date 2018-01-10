# Copyright 2017 Mycroft AI, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os.path import join, exists
from os import makedirs
from mycroft.skills.core import FallbackSkill
from mycroft.util.parse import normalize
import random


class LearnUnknownSkill(FallbackSkill):
    def __init__(self):
        super(LearnUnknownSkill, self).__init__()
        # start a utterance database
        self.entity_words = []
        if "utterance_db" not in self.settings:
            self.settings["utterance_db"] = {self.lang: {}}
        if "entity_db" not in self.settings:
            self.settings["entity_db"] = {self.lang: {}}

    def initialize(self):
        self.entity_words = self.read_voc_lines("entity_words")

        # high priority to always call handler, tweak number if you only
        # want utterances after a certain fallback

        self.register_fallback(self.handle_fallback, 1)

        # register learned utterances
        self.create_learned_intents()

        # TODO intent to register learned utterances
        # TODO intent to ask answer samples and update db
        # create intent for handle_learn
        # TODO intent  the answer for X is Y intent
        # add X utterance with Y answer handler and create intent
        # TODO intent  add stuff to .entity files
        # "chicken is an example of animal" -> if animal.entity does not exist
        # create it, add "chicken" to that file

    def read_voc_lines(self, name):
        with open(join(self.vocab_dir, name + '.voc')) as f:
            return filter(bool, map(str.strip, f.read().split('\n')))

    def parse_entities(self, answer):
        # do some parsing so if in the user spoken answer there
        # is "X entity", replace "X entity" by "{X}"
        words = answer.split(" ")
        for idx, word in enumerate(words):
            if idx <= 0:
                continue
            word_prev = words[idx - 1]
            if word in self.entity_words:
                entity = word_prev
                words[idx] = ""
                words[idx - 1] = "{" + entity + "}"
                if entity not in self.settings["entity_db"][
                    self.lang.keys()]:
                    self.settings["entity_db"][self.lang][entity] = []

        return " ".join(words)

    def handle_learn(self, message):
        utterances = self.settings["utterance_db"][self.lang]
        # if there are utterances in db
        if len(utterances):
            # pick a random one
            utterance = random.choice(utterances.keys())
            answers = utterances[utterance]
            # if less than 2 sample answers
            if len(answers) < 2:
                # ask user for answer
                question = self.dialog_renderer.render("what.answer", {"question": utterance})
                answer = self.get_response(question)
                if answer:
                    answer = self.parse_entities(answer)
                    # if user answered add to database
                    self.add_utterances_to_db(utterance, answer, self.lang)
        else:
            self.speak_dialog("nothing.to.learn")

    def add_utterances_to_db(self, utterances, answers=None, lang=None):
        # accept string or list input
        if not isinstance(answers, list):
            answers = [answers]

        if not isinstance(utterances, list):
            utterances = [utterances]

        lang = lang or self.lang

        # store utterances in db for later learning
        if lang not in self.settings["utterance_db"]:
            self.settings["utterance_db"][lang] = {}

        for utterance in utterances:
            if utterance not in self.settings["utterance_db"][lang]:
                self.settings["utterance_db"][lang][utterance] = answers
            else:
                self.settings["utterance_db"][lang][utterance] += answers

        # optionally do a manual settings save
        self.settings.store()

    def create_learned_intents(self):
        # check paths exist
        if not exists(join(self._dir, "vocab", self.lang)):
            makedirs(join(self._dir, "vocab", self.lang))

        if not exists(join(self._dir, "dialog", self.lang)):
            makedirs(join(self._dir, "dialog", self.lang))

        # create entities
        entitys = self.settings["entity_db"][self.lang]
        for entity in entitys:
            values = entitys[entity]
            if len(values):
                # create intent file for padatious
                path = join(self._dir, "vocab", self.lang,
                            entity + ".entity")
                with open(path, "r") as f:
                    lines = f.readlines

                with open(path, "a") as f:
                    for value in values:
                        if value not in lines:
                            f.write(value+"\n")

                self.register_entity_file(entity + ".entity")

        # create .intent and .dialog
        utterances = self.settings["utterance_db"][self.lang]
        for utterance in utterances:
            answers = utterances[utterance]
            if len(answers):
                utterance = self.parse_entities(utterance)
                # create intent file for padatious
                path = join(self._dir, "vocab", self.lang,
                            utterance+".intent")
                with open(path, "a") as f:
                    f.write(utterance+"\n")

                # create learned answers dialog file
                path = join(self._dir, "dialog", self.lang,
                            utterance + ".dialog")

                with open(path, "r") as f:
                    lines = f.readlines

                with open(path, "a") as f:
                    for answer in answers:
                        if answer not in lines:
                            f.write(answer + "\n")

                # create simple handler that speak dialog
                def handler(message):
                    data = {}
                    for entity in entitys:
                        if message.data.get(entity):
                            data[entity] = message.data.get(entity)
                    self.speak_dialog(utterance, data)

                # register learned intent
                self.register_intent_file(utterance + '.intent', handler)

    def handle_fallback(self, message):
        lang = message.data.get("lang", self.lang)
        utterance = normalize(message.data['utterance'], lang=lang)

        # add utterance to db without answers
        self.add_utterances_to_db(utterance, lang=lang)

        # always return False so other fallbacks may still trigger
        return False


def create_skill():
    return LearnUnknownSkill()
