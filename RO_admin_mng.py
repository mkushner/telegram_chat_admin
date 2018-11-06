from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import telegram
import requests


token = "token_here" # TelegramBot Token
group_id = "id_here" # provide GroupID
updater = Updater(token = token)  
dispatcher = updater.dispatcher


# start command handle
def startCommand(bot, update):   

    print(f"BOT: start session from user: {update.message.chat_id}")
    
    if ( update.message.chat_id != group_id ):

        access_keyboard = telegram.InlineKeyboardButton(text="Request access", callback_data="ffabb044431")
        custom_keyboard = [[access_keyboard]]
        reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard) 
        
        bot.send_message(chat_id=update.message.chat_id, text='Press the button for requesting an access', reply_markup=reply_markup)
   

# request access button
def button(bot, update):
    query = update.callback_query

    print(f"BOT: requested access from user: {query.message.chat_id}")

    try:
        accessRequest = grantUserAccess(group_id, query.message.chat_id, query.data)
        print (accessRequest)
    except:
        raise
    
    if ( accessRequest == "AccessGranted"):
        bot.edit_message_text(text=f"Access granted", chat_id=query.message.chat_id, message_id=query.message.message_id, parse_mode = 'Markdown')
    elif ( accessRequest == "CallFromPrivate"):
        bot.edit_message_text(text=f"Please start a private session", chat_id=query.message.chat_id, message_id=query.message.message_id)
    elif ( accessRequest == "FatalError"):
        bot.edit_message_text(text=f"Error processing request", chat_id=query.message.chat_id, message_id=query.message.message_id)
    elif ( accessRequest == "JoinFirst"):
        bot.edit_message_text(text=f"Join the group before requesting an access", chat_id=query.message.chat_id, message_id=query.message.message_id)
    elif ( accessRequest == "Admin"):
        bot.edit_message_text(text=f"Administrator already has rights", chat_id=query.message.chat_id, message_id=query.message.message_id)
    elif ( accessRequest == "Banned"):
        bot.edit_message_text(text=f"Banned user", chat_id=query.message.chat_id, message_id=query.message.message_id)
    else:
        bot.edit_message_text(text=f"Fatal error", chat_id=query.message.chat_id, message_id=query.message.message_id)

# monitor new members arrival
def getNewMembers (bot, update):

    membersArray = []

  # fill in new members array
    for member in update.message.new_chat_members:
        membersArray.append(member.id)
    
  # Restrict access for a new member
  ## TBD: clear access limitation for members left ## 
    banned = restrictUserAccess( update.message.chat_id, membersArray )
    print (banned)

    banned_names = getBannedUserById ( update.message.chat_id, banned )
    print (banned_names)
  
  # only 1 user in array possible (?)   
    bot.send_message(chat_id=update.message.chat_id, text='Hi, ' + banned_names[0] + '! Read-only access by default. \nPlease start a session with @ROadminBot for access request.', parse_mode = 'Markdown')
        

# read-only mode by default 
def restrictUserAccess (chat_id, user_list):

    banlist = []
    url = "https://api.telegram.org/bot"+token+"/restrictChatMember"

    for banhammer in user_list:
        params = {'chat_id': chat_id, 'user_id': banhammer}
        response = requests.post(url, params = params)
        if (response):
            banlist.append(banhammer)

    print ("BOT: missiles launched")
    return banlist


# get username by uID
def getBannedUserById (chat_id, banned_user_list):

    ban_name_list = []
    url = "https://api.telegram.org/bot"+token+"/getChatMember"
    
    for nameresolve in banned_user_list:
        params = { 'chat_id': chat_id, 
                   'user_id': nameresolve }
        response = requests.post(url, params = params)
        responseJson = response.json()
      # print (responseJson)

        if (responseJson):
            ban_name_list.append(responseJson['result']['user']['first_name'])
  
    return ban_name_list


# full access by request 
## TBD: check user access to avoid excess call ## 
def grantUserAccess (chat_id, user_id, accessID):    

    userStatus = getUserStatus (chat_id, user_id)
    print (f"grant access with: {userStatus}") 

    if ( userStatus ):
        
        if ( userStatus['result']['status'] == 'restricted' ):

            if (accessID == 'ffabb044431'):   
                url = "https://api.telegram.org/bot"+token+"/restrictChatMember"
                params = { 'chat_id': chat_id, 
                        'user_id': user_id, 
                        'can_send_messages': True, 
                        'can_send_media_messages': True, 
                        'can_send_other_messages': True, 
                        'can_add_web_page_previews': True }

                response = requests.post(url, params = params)
                responseJson = response.json()    

                if (responseJson['ok']):
                    return "AccessGranted"
                else:
                    return "ApiError"
            else:
                return "IncorrectAccessRequestCode"
        
        elif ( userStatus['result']['status'] == 'left' ):               
            return "JoinFirst"

        elif ( userStatus['result']['status'] == 'creator' or userStatus['result']['status'] == 'administrator' ):
            return "Admin"
        
        elif ( userStatus['result']['status'] == 'kicked' ):               
            return "Banned"
        
        else:
            return "FatalError"
        
    else:
        return "FatalError"

def getUserStatus (chat_id, user_id):
    
    url = "https://api.telegram.org/bot"+token+"/getChatMember"
        
    params = { 'chat_id': chat_id, 
                'user_id': user_id }
    response = requests.post(url, params = params)
    responseJson = response.json()

    if (responseJson['ok'] == True):
        return responseJson
    else:
        return False

# handlers
start_command_handler = CommandHandler('start', startCommand)
button_handler = CallbackQueryHandler(button)
access_handler = MessageHandler(Filters.status_update.new_chat_members, getNewMembers)

# dispatcher
# updater.dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(start_command_handler)
dispatcher.add_handler(button_handler)
dispatcher.add_handler(access_handler)

# update fire
updater.start_polling(clean=True)