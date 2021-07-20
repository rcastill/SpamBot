# What is this?

This is a joke between friends to make annoying reminders. The user (master) will give the bot a message to spam, then the bot will send a message every `/spamint` seconds and delete it after `/delint` seconds since sent. Multiple messages can be configured, each having independent interval settings.

The dependencies are ancient: the code has not been updated since sept, 2017.

## Development Environment

Activate (setup if is the first time) the virtual env:

```bash
$(./scripts/setup-devenv.sh)
```

This will install virtualenv and dependencies listed in requirements.txt. Then it will source it.
If dependencies are already installed, this will only activate the existing virtualenv.

## Run

With virtualenv activated run:

```bash
(venv) SPAMBOT_TOKEN='your-bot-token-here' python main.py
```

### Example

Start a chat with the bot then:

1. Case 1: Simple message with default intervals (spam interval 5s, delete interval 1s)

```
you: /spam simple
# second 0
bot: simple
# second: 1
bot: *deletes message*
# second 5
bot: simple
# repeat
```

2. Case 2: Larger message with id and custom intervals

```
you: /spam some big message #big
# second 0
bot: some big message
you: /spamint #big 10
bot: New interval set for #big: 10.0 seconds
you: /delint #big 25
bot: New interval set for #big: 10.0 seconds
# now bot will send every 10 seconds and delete after 25 (overlap)
```

To stop messages, run:

```
you: /stop simple
you: /stop #big
```