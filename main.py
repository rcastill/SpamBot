from telegram.ext import Updater, CommandHandler
from telegram.error import BadRequest
from set_interval import Interval
from threading import Timer, Lock
import logging
import os

# logging config
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DEFAULT_INTERVAL = 5  # seconds
DEFAULT_DELETE_TIME = 1


class Message:
    def __init__(self, id, on_delete, delete_time):
        self.id = id
        self.on_delete = on_delete
        self.restart(delete_time)

    def restart(self, delete_time):
        # If timer exists, cancel it
        if hasattr(self, 'timer'):
            self.stop()
        # Reset timer
        self.timer = Timer(delete_time,
                           self.on_delete, (self.id,))
        self.timer.start()

    def stop(self):
        self.timer.cancel()


class Spam:
    def __init__(self, id, user_id, spam_msg, msg_id, bot):
        self.id = id
        self.creator = user_id
        self.spam_msg = spam_msg
        self.msg_id = msg_id
        self.bot = bot
        self.delete_time = DEFAULT_DELETE_TIME
        self.messages = {
            # message_id: Message
        }
        self.msgs_mutex = Lock()

        # Send when registered
        self.interval = Interval(self.send_message,
                                 DEFAULT_INTERVAL)

    def send_message(self):
        self.msgs_mutex.acquire()
        m = self.bot.send_message(chat_id=self.id, text=self.spam_msg)
        self.messages[m.message_id] = Message(
            m.message_id, self.delete_message, self.delete_time)
        self.msgs_mutex.release()

    def delete_message(self, message_id, lock=True):
        try:
            self.bot.delete_message(chat_id=self.id, message_id=message_id)
        except BadRequest:
            logging.log(logging.ERROR, 'BadRequest while deleting message!')

        # Delete from register
        if lock:
            self.msgs_mutex.acquire()
        if message_id in self.messages:
            del self.messages[message_id]
        if lock:
            self.msgs_mutex.release()

    def set_spam_interval(self, secs):
        self.interval.set(secs)

    def set_delete_interval(self, secs):
        self.delete_time = secs
        self.delete_messages()

    def get_key(self):
        return (self.id, self.spam_msg)

    def get_short_key(self):
        if self.msg_id is None:
            return
        return (self.id, self.creator,
                self.msg_id)

    def delete_messages(self):
        self.msgs_mutex.acquire()
        # Avoid delete while iterating
        while len(self.messages) > 0:
            message = list(self.messages.values())[0]
            message.stop()
            self.delete_message(message.id,
                                lock=False)
        self.msgs_mutex.release()

    def stop(self):
        self.delete_messages()
        self.interval.cancel()


spams = {
    # id: Spam
}


def spam(bot, update):
    spam_msg = update.message.text.split('/spam')[1].strip()
    if spam_msg == '':
        update.message.reply_text('Give me a message!')
        return

    # Get msg_id
    spam_split = spam_msg.split('#')
    msg_id = None

    if len(spam_split) > 1:
        # Last after # is msg_id
        msg_id = spam_split[-1].strip()
        spam_msg = '#'.join(spam_split[:-1])

    # Get chat_id
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # Generate long key
    spam_key = (chat_id, spam_msg)
    # Generate short key
    short_key = None

    if msg_id is not None:
        short_key = (chat_id, user_id, msg_id)

    # Create the chat object
    spam = Spam(chat_id, user_id, spam_msg, msg_id, bot)
    spams[spam_key] = spam

    if short_key is not None:
        spams[short_key] = spam


def stop(bot, update):
    arg = update.message.text.split('/stop')[1].strip()
    if arg == '':
        update.message.reply_text('Which message?')
        return

    # Get chat_id
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if arg.startswith('#'):
        key = (chat_id, user_id, arg[1:].strip())
    else:
        key = (chat_id, arg)

    if key in spams:
        spam = spams[key]

        if spam.creator == user_id:
            spam.stop()

            # Delete both references if necessary
            spam_key = spam.get_key()
            short_key = spam.get_short_key()

            del spams[spam_key]
            if short_key is not None:
                del spams[short_key]

            update.message.reply_text("As you request, master.")
        else:
            update.message.reply_text('You are not my creator!')
    else:
        update.message.reply_text('No such spam!')


def get_positive_number_or_none(s):
    try:
        f = float(s)
        # Check not NaN
        if f == float('NaN'):
            return
        elif f <= 0:
            return

        return f
    except ValueError:
        return


def set_interval(bot, update, comm, method):
    args = update.message.text.split(comm)
    if len(args) == 1:
        logging.log(logging.ERROR, 'Invalid method: %s' % method)
    else:
        args = args[1].strip()

    if args == '':
        update.message.reply_text(
            'Usage: {} (#message_id|message) interval'.format(comm))
        return

    args_split = args.split()
    if len(args_split) <= 1:
        update.message.reply_text(
            'Usage: {} (#message_id|message) interval'.format(comm))
        return

    interval = get_positive_number_or_none(args_split[-1].strip())

    if interval == None:
        update.message.reply_text('Invalid interval!')
        return

    # Get chat_id
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    spam_s = ''.join(args_split[:-1]).strip()
    if spam_s.startswith('#'):
        key = (chat_id, user_id, spam_s[1:].strip())
    else:
        key = (chat_id, spam_s)

    if key in spams:
        spam = spams[key]
        spam_set_interval = getattr(spam, method, None)
        if spam_set_interval == None:
            logging.log(logging.ERROR, 'Invalid method: %s' % method)
            return

        update.message.reply_text(
            'New interval set for {}: {} seconds'.format(spam_s, interval))
        spam_set_interval(interval)
    else:
        update.message.reply_text('No such spam!')


def spam_interval(bot, update):
    set_interval(bot, update, '/spamint', 'set_spam_interval')


def delete_interval(bot, update):
    set_interval(bot, update, '/delint', 'set_delete_interval')


if __name__ == '__main__':
    # Create updater
    tokenvar = 'SPAMBOT_TOKEN'
    token = os.getenv(tokenvar, None)
    if token is None:
        raise RuntimeError('{} must be defined'.format(tokenvar))
    updater = Updater(token)
    # Register commands
    updater.dispatcher.add_handler(CommandHandler('spam', spam))
    updater.dispatcher.add_handler(CommandHandler('stop', stop))
    updater.dispatcher.add_handler(CommandHandler('spamint',
                                                  spam_interval))
    updater.dispatcher.add_handler(CommandHandler('delint',
                                                  delete_interval))

    # Start updater
    updater.start_polling()
    updater.idle()
