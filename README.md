# learn fallback
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1QJNhKM8tVv62XSUrST2vnaMXh5ADSyYP8)](https://en.cryptobadges.io/donate/1QJNhKM8tVv62XSUrST2vnaMXh5ADSyYP8)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://paypal.me/jarbasai)
<span class="badge-patreon"><a href="https://www.patreon.com/jarbasAI" title="Donate to this project using Patreon"><img src="https://img.shields.io/badge/patreon-donate-yellow.svg" alt="Patreon donate button" /></a></span>
[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/JarbasAl)

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

