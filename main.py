import os.path
import telegram
import redis
import gettext
import configparser
import logging

from functools import wraps
from telegram.ext import Updater, CommandHandler, MessageHandler,\
                         RegexHandler, Filters

# Configurando o bot
config = configparser.ConfigParser()
config.read_file(open('config.ini'))

# Contador 
#contador = 1

# Conectando ao API do telegram
# Updater recebe informação e dispatcher conecta comandos
updater = Updater(token=config['DEFAULT']['token'])
dispatcher = updater.dispatcher

def _(msg): return msg


# Conectando ao bando de dados do redis
db = redis.StrictRedis(host=config['DB']['host'],
                       port=config['DB']['port'],
                       db=config['DB']['db'])





def start(bot, update):
    """
        Mostra uma mensagem de bem vindo e demonstra os comandos
    """
    me = bot.get_me()

    # Mensagem de bem vindo
    msg = _("Olá!\n")
    msg += _("Eu sou {0} e estou aqui para ajuda-lo.\n").format(me.first_name)
    msg += _("O que gostaria que fizesse?\n\n")
    msg += _("/suporte - Abre um novo ticket de suporte\n")
    msg += _("/opcoes - Abre as opçoes de configuração\n\n")

    # Menu de comandos
    main_menu_keyboard = [[telegram.KeyboardButton('/support')],
                          [telegram.KeyboardButton('/settings')]]
    reply_kb_markup = telegram.ReplyKeyboardMarkup(main_menu_keyboard,
                                                   resize_keyboard=True,
                                                   one_time_keyboard=True)

    # Enviar a mensagem pelo menu
    bot.send_message(chat_id=update.message.chat_id,
                     text=msg,
                     reply_markup=reply_kb_markup)



def support(bot, update):
    """
        Envia uma mensagem de suporte. Um tipo de "Como posso te ajudar?".
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=_("Por favor, diga me o que você precisa :)"))



def support_message(bot, update):
    """
        Recebe a mensagem do usua
        Se a mensagem e uma resposta do usuario, o bot 
        fala-ra com o usuario mandando o conteudo 
        da mensagem. Se a mensagem é um pedido do usuario 
        o bot enviara a mensagem para o grupo de suporte
    """
    if update.message.reply_to_message and \
       update.message.reply_to_message.forward_from:
        # Se é uma respota do usuario, o bot responderá a mensagem.
        bot.send_message(chat_id=update.message.reply_to_message
                         .forward_from.id,
                         text=update.message.text)
    else:
        # Se for um pedido, o bot irá enviar a mensagem
        # para o grupo de suporte
        bot.forward_message(chat_id=int(config['DEFAULT']['support_chat_id']),
                            from_chat_id=update.message.chat_id,
                            message_id=update.message.message_id)                            
        bot.send_message(chat_id=update.message.chat_id,
                         text=_("De-me um tempo para pensar, em breve virei com uma resposta para lhe dar."))
        escreve_log(str(update.message.text), str(update.message.chat_id))
      

def escreve_log(mensagem, id):
     log = open('log.txt', 'a').write("| " + "usuario " + ': ' + id + ' | Pergunta: ' + mensagem + ' | \n')
     log.close()




def settings(bot, update):
    """
        Configura a linguagem das mensagem usando um teclado customizado.
    """
    # Para definir a linguagem das mensagens.
    msg = _("Por favor. escolha a linguagem:\n")
    msg += "en_US - English (US)\n"
    msg += "pt_BR - Português (Brasil)\n"

    # Menu das linguagens
    languages_keyboard = [
        [telegram.KeyboardButton('en_US - English (US)')],
        [telegram.KeyboardButton('pt_BR - Português (Brasil)')]
    ]
    reply_kb_markup = telegram.ReplyKeyboardMarkup(languages_keyboard,
                                                   resize_keyboard=True,
                                                   one_time_keyboard=True)

    # Envia a mensagem com o menu de linguagem
    bot.send_message(chat_id=update.message.chat_id,
                     text=msg,
                     reply_markup=reply_kb_markup)



def kb_settings_select(bot, update, groups):
    """
        Atualiza a linguagem do usuario baseado em sua escolha
    """
    chat_id = update.message.chat_id
    language = groups[0]

    # Linguagens disponiveis
    languages = {"pt_BR": "Português (Brasil)",
                 "en_US": "English (US)"}

    # Se a linguagem bate com a expressão e é uma opção valida
    if language in languages.keys():
        # Defina a linguagem do usuario
        db.set(str(chat_id), language)
        bot.send_message(chat_id=chat_id,
                         text=_("Lingua atualizada para {0}")
                         .format(languages[language]))
    else:
        # Se não é uma escolha valida ele envia-ra a seguinte mensagem.
        bot.send_message(chat_id=chat_id,
                         text=_("Linguagem desconhecida! :("))



def unknown(bot, update):
    """
        Commando de amostra, para caso o usuario mandar uma mensagem invalida..
    """
    msg = _("Desculpe, eu não compreendi o que você pediu.")
    bot.send_message(chat_id=update.message.chat_id,
                     text=msg)
# Criando apoios
start_handler = CommandHandler('start', start)
#contador = 1
support_handler = CommandHandler('support', support)
support_msg_handler = MessageHandler([Filters.text], support_message)
settings_handler = CommandHandler('settings', settings)
get_language_handler = RegexHandler('^([a-z]{2}_[A-Z]{2}) - .*',
                                    kb_settings_select,
                                    pass_groups=True)
help_handler = CommandHandler('help', start)
unknown_handler = MessageHandler([Filters.command], unknown)

# Adicionando apoios
dispatcher.add_handler(start_handler)
dispatcher.add_handler(support_handler)
dispatcher.add_handler(settings_handler)
dispatcher.add_handler(get_language_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(unknown_handler)

# O apoio de mensagem deve ser o ultimo
dispatcher.add_handler(support_msg_handler)



# Para rodar esse programa:
updater.start_polling()
#contador+=1
# Para para-lo:
#updater.stop()
