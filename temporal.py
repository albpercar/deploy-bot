from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = '7338148224:AAEXnqui8026QPC2fUjzUM3-c53OhuH70fs'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hola! Soy un bot, envíame un mensaje para obtener el ID del grupo.')

def echo(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    update.message.reply_text(f'El ID de este grupo es: {chat_id}')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
