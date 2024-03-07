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
from ovos_utils.log import LOG
from ovos_workshop.skills.fallback import FallbackSkill
import random


class LearnUnknownSkill(FallbackSkill):

    def initialize(self):
        # ensure paths exist
        if not exists(join(self._dir, "vocab", self.lang)):
            makedirs(join(self._dir, "vocab", self.lang))

        if not exists(join(self._dir, "dialog", self.lang)):
            makedirs(join(self._dir, "dialog", self.lang))

        # start a utterance database
        self.entity_words = []

        if "utterance_db" not in self.settings:
            self.settings["utterance_db"] = {self.lang: {}}
        if "entity_db" not in self.settings:
            self.settings["entity_db"] = {self.lang: {}}

        # init default values
        self.settings["answer_depth"] = self.settings.get("answer_depth", 5)
        self.settings["priority"] = self.settings.get("priority", 5)

        self.questions = []

        # read entity parsing keywords
        self.entity_words = self.read_voc_lines("entity_words")

        # questions, this is replaced with an entity to try help avoid some
        # mistakes in padatious
        self.register_entity_file("question_verb.entity")

        # high priority to always call handler, tweak number if you only
        # want utterances after a certain fallback
        self.register_fallback(self.handle_fallback,
                               self.settings["priority"])

        # register learned utterances
        self.create_learned_intents()

        # intent to (re)register learned utterances
        self.register_intent_file("learn.intent", self.handle_learn)

        # intent to ask answer samples and update db
        # create intent for handle_learn
        self.register_intent_file("update_learn.intent",
                                  self.handle_update_learned)

        # the answer for X is Y intent
        # add X utterance with Y answer handler and create intent
        self.register_intent_file("answer_is.intent",
                                  self.handle_new_answer)

        # intent add stuff to .entity files
        # "chicken is an example of animal" -> if animal.entity does not exist
        # create it, add "chicken" to that file
        self.register_intent_file("entity_is.intent",
                                  self.handle_new_entity)

    def read_voc_lines(self, name):
        with open(join(self._dir, "vocab", self.lang, name + '.voc')) as f:
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

    def add_utterances_to_db(self, utterances=None, answers=None, lang=None):
        # accept string or list input
        answers = answers or []
        utterances = utterances or []
        if not isinstance(answers, list):
            answers = [answers]

        if not isinstance(utterances, list):
            utterances = [utterances]

        lang = lang or self.lang

        # store utterances in db for later learning
        if lang not in self.settings["utterance_db"]:
            self.settings["utterance_db"][lang] = {}

        for utterance in utterances:
            LOG.info("Adding utterance to db: " + str(utterance))
            LOG.info("Adding answers to db: " + str(answers))
            if utterance not in self.settings["utterance_db"][lang]:
                self.settings["utterance_db"][lang][utterance] = answers
            else:
                # merge without duplicates
                for answer in answers:
                    if answer not in self.settings["utterance_db"][lang][utterance]:
                        self.settings["utterance_db"][lang][utterance].append(answer)

        # optionally do a manual settings save
        self.settings.store()

    def create_learned_intents(self):
        # create entities
        entitys = self.settings["entity_db"][self.lang]
        for entity in entitys:
            values = entitys[entity]
            LOG.info("Entities to learn: " + str(values))
            if len(values):
                # create intent file for padatious
                path = join(self._dir, "vocab", self.lang,
                            entity + ".entity")
                if exists(path):
                    with open(path, "r") as f:
                        lines = f.readlines()
                else:
                    lines = []

                with open(path, "a") as f:
                    for value in values:
                        if value not in lines:
                            f.write(value + "\n")

                self.register_entity_file(entity + ".entity")

        # create .intent and .dialog
        utterances = self.settings["utterance_db"][self.lang]
        for utterance in utterances:
            if utterance:
                LOG.info("unknown utterance: " + str(utterance))
                answers = utterances[utterance]
                LOG.info("possible answers: " + str(answers))
                if len(answers):
                    utterance = self.parse_entities(utterance)
                    # create intent file for padatious
                    path = join(self._dir, "vocab", self.lang,
                                utterance + ".intent")

                    if exists(path):
                        with open(path, "r") as f:
                            lines = f.readlines()
                    else:
                        lines = []

                    if utterance not in lines:
                        with open(path, "a") as f:
                            f.write(utterance + "\n")

                    # create learned answers dialog file
                    path = join(self._dir, "dialog", self.lang,
                                utterance + ".dialog")

                    if exists(path):
                        with open(path, "r") as f:
                            lines = f.readlines()
                    else:
                        lines = []

                    with open(path, "a") as f:
                        for answer in answers:
                            if answer not in lines:
                                f.write(answer + "\n")

                    # create simple handler that speak dialog
                    def handler(message, dummy=None):
                        # dummy is a hack because of not having self
                        data = {}
                        for entity in entitys:
                            if message.data.get(entity):
                                data[entity] = message.data.get(entity)
                        self.speak_dialog(utterance, data)

                    # remove and re-register learned intent
                    self.remove_event(
                        str(self.skill_id) + ':' + utterance + '.intent')
                    self.register_intent_file(utterance + '.intent', handler)

    def handle_new_entity(self, message):
        value = message.data.get("value")
        entity = message.data.get("entity")
        lang = message.data.get("lang", self.lang)
        if entity not in self.settings["entity_db"][self.lang].keys():
            self.settings["entity_db"][self.lang][entity] = [value]
        else:
            self.settings["entity_db"][self.lang][entity].append(value)

        values = self.settings["entity_db"][self.lang][entity]
        path = join(self._dir, "vocab", lang, entity + ".entity")

        if not exists(path):
            with open(path, "w") as f:
                f.writelines(values)
        else:
            with open(path, "r") as f:
                lines = f.readlines()

            with open(path, "a") as f:
                for value in values:
                    if value not in lines:
                        f.write(value + "\n")

        self.register_entity_file(entity + ".entity")
        self.speak_dialog("new.entity", {"entity": entity, "value": value})

    def handle_new_answer(self, message):
        answer = message.data.get("answer")
        answer = self.parse_entities(answer)
        question = message.data.get("question")
        question = self.parse_entities(question)
        self.add_utterances_to_db(question, answer)
        self.create_learned_intents()
        self.speak_dialog("new.answer", {"question": question, "answer":
            answer})

    def handle_update_learned(self, message):
        # register in padatious
        self.create_learned_intents()
        self.speak_dialog("update_learned")

    def handle_learn(self, message):
        utterances = self.settings["utterance_db"][self.lang]
        # if there are utterances in db
        if len(utterances):
            LOG.info("utterances to learn: " + str(utterances))
            # pick a random one
            utterance = random.choice(utterances.keys())
            answers = utterances[utterance]
            # if less than X sample answers
            if len(answers) <= self.settings["answer_depth"]:
                # ask user for answer
                answer = self.get_response("what.is", {"question": utterance})
                if answer:
                    answer = self.parse_entities(answer)
                    # if user answered add to database
                    self.add_utterances_to_db(utterance, answer, self.lang)
                    self.speak_dialog("new.answer",
                                      {"question": utterance, "answer":
                                          answer})
                    # register in padatious
                    self.create_learned_intents()
                    return

        self.speak_dialog("nothing.to.learn")

    def handle_fallback(self, message):
        lang = message.data.get("lang", self.lang)
        utterance = message.data['utterance']

        # add utterance to db without answers
        self.add_utterances_to_db(utterance, lang=lang)

        # always return False so other fallbacks may still trigger
        return False

