# learn fallback

learning skill, capture all intent_failure utterances into a database


creates .intent and .dialog files with answers and registers padatious intents for learned answers


# Usage

- time to learn -> check for utterances in db and ask you for a correct answer
- update learned things -> (re)register utterances with answers
- answer of {question} is {answer} -> create question.intent with question and question.dialog with answer, register padatious intent
- {value} is an example of {entity} -> add value to, and register "entity".entity
- on every fallback -> passive capture of all answers

# TODO


parsing for entity commands in teaching intents (animal entity = {animal})


debug


use settingsmeta to add utterances in web settings

