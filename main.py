from os import environ
import telebot
from telebot.types import  InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from pymongo import MongoClient
from random import choice 
from logging import info , basicConfig , INFO
from random import shuffle

from telebot import types

# logging config 
basicConfig(level= INFO,
            format= '%(asctime)s %(levelname)s %(message)s',
            datefmt= '%Y-%m-%d %H:%M')

# telebot setup
botToken = environ['token']
bot = telebot.TeleBot(botToken,  parse_mode=None)

# mongodb client setup
client = MongoClient('mongodb+srv://tkt_bot_version1:{}@cluster0.tu30q.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'.format(environ['pw']))
db = client['21pts_bot']
room_db = db['room']
stats_db = db['stats']

# check if account is created 
def check_ac(message):
    id = message.id
    myquery = {'_id' : id}
    if stats_db.count_documents(myquery) == 0 :
            data = {'_id' : id , 'win':0 , 'room': [] , 'name' : message.first_name}
            info("User {} with id {} created account".format(message.first_name , str(id)))
            stats_db.insert_one(data)

# check if user is in a room
def check_room(id):
    myquery = {'_id' : id}

    data = stats_db.find_one(myquery)
    if data['room'] != []:
        return data['room']
    else :
        return False

# check owner
def check_owner(room_num):
    myquery = {'_id' : room_num}
    data = room_db.find_one(myquery)

    return data['owner'][0]

def num_to_card(num):
    ans = [num[0],num[1]]

    if num[0] == 1:
        ans[0] = 'A'
    elif num[0] == 11:
        ans[0] = 'J'
    elif num[0] == 12:
        ans[0] = 'Q'
    elif num[0] == 13:
        ans[0] = 'K'

    if num[1] == 1:
        ans[1] = '♦️'
    elif num[1] == 2:
        ans[1] = '♣️'
    elif num[1] == 3:
        ans[1] = '♥️'
    elif num[1] == 4:
        ans[1] = '♠️'

    return ans[1]+str(ans[0])

# number to cards for user readable
def num_to_cards(arr):
    ans = ''
    for num in arr:
        if num[0] == 1:
            num[0] = 'A'
        elif num[0] == 11:
            num[0] = 'J'
        elif num[0] == 12:
            num[0] = 'Q'
        elif num[0] == 13:
            num[0] = 'K'

        if num[1] == 1:
            num[1] = '♦️'
        elif num[1] == 2:
            num[1] = '♣️'
        elif num[1] == 3:
            num[1] = '♥️'
        elif num[1] == 4:
            num[1] = '♠️'

        ans += num[1]+str(num[0])+ ' '
    return ans

# number to pts 
def num_to_pts(arr):
    total = 0
    ace = 0

    for num in arr:
        if num[0] == 1:
            ace += 1 
        else :
            if num[0] > 10:
                total += 10
            else:
                total += int(num[0])

    if ace == 0:
        return str(total)
    else:
        return str(ace_values(ace , total))


# calculate ace 
def ace_values(ace , total):
    temp_list = []

    for i in range(ace+1):
        temp_list.append(11*i + ace-1)
    
    
    return get_ace_values(temp_list , total)

# get total value
def get_ace_values(temp_list , total):
    value_list = []

    for ace_value in temp_list:
        value_list.append(total+ace_value)
        
    return max(value for value in value_list if value<=21)
    
        

@bot.message_handler(commands=['start','help'])
def start(message):
    bot.reply_to(message , ''' \
21pts Bot

The bot is made by kotnid 

Command available:
        /help - show this message
        /open_21 - open a room
        /join_21 - join a room
        /kick_21 - kick player in room
        /start_21 - start a game
        /end_21 - end a game  
        /leave_21 - leave a room
        /close_21 - close a room
        /stats_21 - show player stats
        /board_21 - show leaderboard

If you have any problem , pls contact tkt0506
\ ''')



# open a room for gaming
@bot.message_handler(commands=['open_21'])
def open(message):
    check_ac(message.from_user)
    if check_room(message.from_user.id) != False:
        bot.reply_to(message , 'You already inside a room :/')
    else:
        if message.chat.type != "group":
            bot.reply_to(message , 'Pls use this function in a group')
        
        else:
            myquery = {'_id' : message.chat.id}
            if room_db.count_documents(myquery) == 0:
                data = {'_id':message.chat.id , 'owner': [message.from_user.id , message.from_user.first_name] , 'players' : [[message.from_user.first_name , message.from_user.id , []]] , 'name' :  message.chat.title , 'status' : '0' , 'cards' : [] , 'number' : 0}
                room_db.insert_one(data)

                stats_db.update_one({'_id' : message.from_user.id } , {'$set' : {'room' : [message.chat.id , message.chat.title]}})

                info("User {} with id {} created room {}".format(message.from_user.first_name , message.from_user.id , message.chat.id))
                bot.reply_to(message , 'Room opened , use /join_21 to join the room')

            else:
                bot.reply_to(message , 'This group open a room already! ')


# join a room 
@bot.message_handler(commands=['join_21'])
def join(message):
    check_ac(message.from_user)
    if check_room(message.from_user.id) != False:
        bot.reply_to(message , 'You alread inside a room :/')
    else:
        if room_db.count_documents({'_id' : message.chat.id}) == 1:
            data = room_db.find_one({'_id' : message.chat.id })

            if data['status'] == '1':
                bot.reply_to(message , 'Pls join after the current game ended')
                return ''

            stats_db.update_one({'_id' : message.from_user.id } , {'$set' : {'room' : [message.chat.id , message.chat.title]}})
            data['players'].append([message.from_user.first_name, message.from_user.id , []])
            room_db.update_one({'_id' : message.chat.id} , {'$set' : {'players' : data['players']}})

            bot.reply_to(message , f'Player {message.from_user.first_name} joined ')
            info("User {} with id {} join room {}".format(message.from_user.first_name ,message.from_user.id , message.chat.id))
        else:
            bot.reply_to(message , 'No room opened at this group')
            



# start the game
@bot.message_handler(commands=['start_21'])
def start(message):
    check_ac(message.from_user)
    if check_room(message.from_user.id) != False:
        myquery = {'_id' : check_room(message.from_user.id)[0]}
        data = room_db.find_one(myquery)

        if check_owner(data['_id']) == message.from_user.id:

            if data['status'] == '1':
                bot.reply_to(message , 'The game start already')
                return ''

            info("User {} with id {} start game in room {}".format(message.from_user.first_name , message.from_user.id , data['_id'] ))

            poker_cards = []

            for i in range(1,14):
                for x in range(1,5):        
                    poker_cards.append([i,x])

            shuffle(poker_cards)

            msg = ''

            for player_list in data['players']:
                    player_list[2] = [poker_cards[0] , poker_cards[1]] 
                    msg += '{} : {}'.format(player_list[0] , num_to_card(poker_cards[0]))+'\n'
                    poker_cards.pop(0)
                    poker_cards.pop(0)

            room_db.update_one({'_id' : message.chat.id} , {'$set' : {'status' : '1' , 'players' : data['players'] , 'cards' : poker_cards}})

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Your option" , switch_inline_query_current_chat = ""))
            bot.send_message(message.chat.id , msg+"\n"+" The first player is {}".format(data['players'][0][0]) + "\n" + "Pls choose your option" , reply_markup=markup)
            


        else:
            bot.reply_to(message , 'You are not the owner of the room')

    else:
        bot.reply_to(message , 'You are not inside a room')



@bot.inline_handler(lambda query : query.query == 'check')
def query_text(inline_query):
    myquery = {'_id' : check_room(inline_query.from_user.id)[0]}
    data = room_db.find_one(myquery)
    
    temp = []

    
    temp.append(types.InlineQueryResultCachedSticker(id = "test" , sticker_file_id='CAACAgUAAxkBAAEELkJiMs1cG97wpjzI1NYPeJTSAAEnvPoAAiMGAAIgJpBV9W9NPtkWUCAjBA'))
        
    bot.answer_inline_query(inline_query.id, temp)

@bot.inline_handler(lambda query : query.query == '')
def query_text(inline_query):
    check_ac(inline_query.from_user)

    if check_room(inline_query.from_user.id) != False:
        if inline_query.chat_type != 'sender':
            myquery = {'_id' : check_room(inline_query.from_user.id)[0]}
            data = room_db.find_one(myquery)

            if data['status'] == '1':
                for player_list in data['players']:
                    if inline_query.from_user.id in player_list:
                        r = types.InlineQueryResultArticle(id = '1', title = 'Check card', input_message_content = types.InputTextMessageContent(f'{inline_query.from_user.first_name} check his card' ) ,  description = str(num_to_cards(player_list[2])))
                        
                        
                        if data['players'].index(player_list) == data['number']:
                            r2 = types.InlineQueryResultArticle('r_get_card', 'Get card', types.InputTextMessageContent('Get Card'))
                            r3 = types.InlineQueryResultArticle('r_pass', 'Pass', types.InputTextMessageContent('Pass'))
                            bot.answer_inline_query(inline_query.id, [r , r2 , r3] , cache_time = 1)
                        
                        else:
                            bot.answer_inline_query(inline_query.id, [r] , cache_time=1)

            else:
                r = types.InlineQueryResultArticle('1', 'The game not start yet', types.InputTextMessageContent('Use /start_21 to start game'))
                bot.answer_inline_query(inline_query.id, [r]  , cache_time=1)

        else:
            r = types.InlineQueryResultArticle('1', 'Pls use in group', types.InputTextMessageContent('Use /join_21 or /open_21 to join a room'))
            #r = types.InlineQueryResultArticle('2', 'Get card', test)
            bot.answer_inline_query(inline_query.id, [r]  , cache_time=1)
            
    else:
        r = types.InlineQueryResultArticle('1', 'You are not inside a room!', types.InputTextMessageContent('Use /join_21 or /open_21 to join a room'))
        bot.answer_inline_query(inline_query.id, [r] , cache_time=1)



@bot.chosen_inline_handler(func = lambda chosen_inline_result : True)
def react(chosen_inline_result):
    if chosen_inline_result.result_id == 'r_get_card':
        room_num = check_room(chosen_inline_result.from_user.id)[0]

        myquery = {'_id' : room_num}
        data = room_db.find_one(myquery)

        picked_card = data['cards'][0]
        data['cards'].pop(0)
        
        room_db.update_one({'_id' : room_num }, {'$set' : {'cards' : data['cards']}})
        
        for player_list in data['players']:
            if chosen_inline_result.from_user.id in player_list:
                data['players'][data['number']][2].append(picked_card)
        room_db.update_one({'_id' : room_num } , { '$set' : {'players' : data['players']}})

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Your option" , switch_inline_query_current_chat = ""))
        bot.send_message(room_num , "Player {} has get 1 card".format(data['players'][data['number']][0]) , reply_markup=markup)
                        
        info("User {} with id {} get card {}".format(data['players'][data['number']][0] , chosen_inline_result.from_user.id , picked_card))

    elif chosen_inline_result.result_id == 'r_pass':
        room_num = check_room(chosen_inline_result.from_user.id)[0]

        myquery = {'_id' : room_num}
        data = room_db.find_one(myquery)

        info("User {} with id {} pass".format(data['players'][data['number']][0] , chosen_inline_result.from_user.id))

        if len(data['players'])-1 == data['number']:
            bot.send_message(room_num , "All players has finished their action , its time to reveal who is the winner")

            msg = ''
            
            player_pts = []
            for player_list in data['players']:
                pts = num_to_pts(player_list[2])
                player_pts.append(pts)
                msg += '{} : {} - {} pts'.format(player_list[0] , num_to_cards(player_list[2]) , pts)+'\n'
            
            try:
                msg += '{} won with {} pts '.format(data['players'][player_pts.index(max(value for value in player_pts if int(value)<=21))][0] , max(value for value in player_pts if int(value)<=21))
                stats_db.update_one({'_id' : data['players'][player_pts.index(max(value for value in player_pts if int(value)<=21))][1]} , {'$inc' : {'win' : 1}})
                
            except:
                msg += 'www everyone lost'

            bot.send_message(room_num , msg)
            if data['players'][player_pts.index(max(value for value in player_pts if int(value)<=21))][0] == 'tkt0506':
                gif_list = ['https://c.tenor.com/CiW__asIWaIAAAAC/k-on-yui-hirasawa.gif' , 'https://c.tenor.com/ssO9d-jnRYIAAAAd/chika-fujiwara-spinning.gif']
                bot.send_video(room_num , choice(gif_list) , None , 'Text')

            players_data = []
            for player_list in data['players']:
                players_data.append([player_list[0] , player_list[1] , []])   

            room_db.update_one({'_id' : data['_id']} , { '$set' : {'players' : players_data , 'cards' : [] , 'status' : '0' , 'number' : 0}})
            
            info("A game ended in room {}".format(data['_id']))

        else:
            room_db.update_one({'_id' : room_num} , {'$inc' : {'number' : 1}})
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Your option" , switch_inline_query_current_chat = ""))
            bot.send_message(room_num , " Next player is {}".format(data['players'][data['number']+1][0]) + "\n" + "Pls choose your option" , reply_markup=markup)


# end the game
@bot.message_handler(commands=['end_21'])
def end(message):
    check_ac(message.from_user)

    if check_room(message.from_user.id)[0] != False:
        if check_owner(check_room(message.from_user.id)[0]) == message.from_user.id:
            myquery = {'_id' : check_room(message.from_user.id)[0]}
            data = room_db.find_one(myquery)

            if data['status'] == '0':
                bot.reply_to(message , 'No game is running in this room')
                return ''

            players_data = []
            for player_list in data['players']:
                players_data.append([player_list[0] , player_list[1] , []])   

            room_db.update_one({'_id' : data['_id']} , { '$set' : {'players' : players_data , 'cards' : [] , 'status' : '0' , 'number' : 0}})
            bot.reply_to(message , 'You end the game')
            info("User {} with id {} ended a game in room {}".format(message.from_user.first_name , message.from_user.id , data['_id']))

        else:
           bot.reply_to(message , 'You are not the owner of the room') 

    else:
        bot.reply_to(message , 'You are not inside a room')



# leave the room
@bot.message_handler(commands=['leave_21'])
def leave(message):
    check_ac(message.from_user)

    if check_room(message.from_user.id)[0] != False:
        myquery = {'_id' : check_room(message.from_user.id)[0]}
        data = room_db.find_one(myquery)
        player_data = []
        room_num = data["_id"]

        for player_list in data['players']:
            if message.from_user.first_name in player_list :
                player_data = player_list

        bot.send_message(room_num , f'Player {message.from_user.first_name} has left the room')        
        data['players'].remove(player_data)

        room_db.update_one({'_id' : data['_id']} , {'$set' : {'players' : data['players']}})
        stats_db.update_one({'_id' : message.from_user.id} , {'$set' : {'room' : []}})
        info("User {} with id {} left the room {}".format(message.from_user.first_name , message.from_user.id , data['_id']))

        if len(data['players']) == 0:
            bot.send_message(room_num , "The room closed as no player inside ._.")
            room_db.delete_one({'_id' : room_num})
            info("Room {} closed".format(room_num))

        elif check_owner(room_num) == message.from_user.id:
            myquery = {'_id' : data['_id']}
            data = room_db.find_one(myquery)

            picker = choice(data['players'])
            bot.send_message(room_num , 'Player {} has become new owner'.format(picker[0]))
            
            room_db.update_one({'_id' : data['_id']} , {'$set' : {'owner' : [picker[0] , picker[1]]}})
            info('Player {} has become new owner in room {}'.format(picker[0] , room_num))
    else:
        bot.reply_to(message , 'You are not inside a room')


# close the room
@bot.message_handler(commands=['close_21'])
def close(message):
    check_ac(message.from_user)

    if check_room(message.from_user.id) != False:
        if check_owner(check_room(message.from_user.id)[0]) == message.from_user.id:
            myquery = {'_id' : check_room(message.from_user.id)[0]}
            data = room_db.find_one(myquery)
            room_num = data['_id']

            for player_list in data['players']:
                stats_db.update_one({'_id' : player_list[1]} , {'$set' : {'room' : []}})

            bot.send_message(room_num , 'Owner has close the room')

            info("User {} with id {} close the room {}".format(message.from_user.first_name , message.from_user.id , data['_id']))
            room_db.delete_one({'_id' : room_num})
            
        else:
           bot.reply_to(message , 'You are not the owner of the room') 

    else:
        bot.reply_to(message , 'You are not inside a room')



# show room information
@bot.message_handler(commands=['room_21'])
def room(message):
    check_ac(message.from_user)

    if check_room(message.from_user.id) != False:
        myquery = check_room(message.from_user.id)[0]
        data = room_db.find_one(myquery)

        players = ""
        for player_list in data['players']:
            players += str(player_list[0]) +'\n'

        if data['status'] == '0':
            status = "Not playing"
        else:
            status = "Playing"

        info("User {} with id {} check the stats of room {}".format(message.from_user.first_name , message.from_user.id , data['_id']))
        bot.reply_to(message , 'Room {} stats'.format(data['name']) + '\n' + 'owner : {} '.format(data['owner'][1]) + '\n' + 'status : {} '.format(status) + '\n' + 'players : ' + '\n'+ players)
    else:
        bot.reply_to(message , 'You are not inside a room')    


# show player stats
@bot.message_handler(commands=['stats_21'])
def stats(message):
    check_ac(message.from_user)

    myquery = {'_id' : message.from_user.id}
    data = stats_db.find_one(myquery)
    bot.reply_to(message , 'Player {} stats'.format(data['name']) + '\n' + 'wins : {}'.format(data['win']) + '\n' + 'Current room : {}'.format(data['room']))
    info("User {} with id {} check the stats".format(message.from_user.first_name , message.from_user.id))


# show the leaderboard
@bot.message_handler(commands=['board_21'])
def board(message):
    check_ac(message.from_user)

    number = message.text.split()[1]
    data = stats_db.find().sort('win' , -1).limit(int(number))
    
    msg =  f'Here is the top {number} players'+'\n'+'\n'
    for i in range(int(number)):
        msg += '{}. {} with {} wins'.format(i+1 , data[i]['name'] , data[i]['win']) + '\n'

    info('User {} with id {} check the leaderboard'.format(str(message.from_user.first_name) , str(message.from_user.id)))
    bot.reply_to(message , msg)



#kick player in room
@bot.message_handler(commands=['kick_21'])
def kick(message):
    check_ac(message.from_user)
    if check_room(message.from_user.id) != False:
        myquery = {'_id' : check_room(message.from_user.id)[0]}
        data = room_db.find_one(myquery)

        if check_owner(data['_id']) == message.from_user.id:
            player = message.text.split()[1]

            if player == message.from_user.first_name:
                bot.reply_to(message , "Bruh u kick yourself which is illegal")

            else:
                for player_list in data['players']:
                    if player in player_list:
                        info("User {} with id {} removed player {} with id {} out of room {}".format(message.from_user.first_name , message.from_user.id , player_list[0] , player_list[1] , data['_id']))
                        
                        bot.send_message(data['_id'] , '{} has been removed'.format(player))

                        data['players'].remove(player_list)
                        room_db.update_one({'_id' : data['_id']} , {'$set' : {'players' : data['players']}})

                        stats_db.update_one({'_id' : player_list[1]} , {'$set' : {'room' : ""}})

                        return ''

                bot.reply_to(message , f'No player named {player}') 

        else:
            bot.reply_to(message , 'You are not the owner of the room')

    else:
        bot.reply_to(message , 'You are not inside a room')


asyncio.run(bot.infinity_polling())

