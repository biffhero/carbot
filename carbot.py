import os
import time
import re
from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from the RTM
MENTION_REGEX = '<@(|[WU].+?)>(.*)'
EXAMPLE_COMMAND = "*'who has ___'* to find a car or *'commands list'*"

def at_user(direct_mention, command):
	print('direct mention')
	at_user_id = direct_mention.group(1)
	at_user = slack_client.api_call('users.info', token = os.environ.get('SLACK_BOT_TOKEN'), user = at_user_id)
	at_username = at_user['user']['profile']['display_name']
	print('at_username ' , at_username)
	x = '<@' + at_user_id + '>'
	print('x= ' ,x)
	command = command.replace(x, at_username)
	print('new message = ' + command)
	return command

def get_names():
	path = 'names.txt'
	name_file = open(path, 'r')
	NAMES = []
	for line in name_file.readlines():
		NAMES.append(line.replace('\n', ''))
	name_file.close()
	return NAMES

def get_inventory():
	path = 'inventory.txt'
	inventory_file = open(path, 'r')
	INVENTORY = {}
	for line in inventory_file.readlines():
		x = line.split('-')
		INVENTORY[x[0]] = x[1].replace('\n', '')
	inventory_file.close()
	return INVENTORY

def update_names(NAMES):
	path = 'names.txt'
	update_file = open(path, 'w')
	for name in NAMES:
		update_file.write(name + '\n')
	update_file.close()

def update_inventory(INVENTORY):
	path = 'inventory.txt'
	update_file = open(path, 'w')
	for key in INVENTORY:
		if INVENTORY[key] == None:
			update_file.write(key + '-' + '\n')
		else:
			update_file.write(key + '-' + INVENTORY[key] + '\n')
	update_file.close()

def car_list():
	path = 'inventory.txt'
	inventory_file = open(path, 'r')
	inventory = inventory_file.read()
	inventory_file.close()
	return inventory

def names_list():
	path = 'names.txt'
	name_file = open(path, 'r')
	names = name_file.read()
	name_file.close()
	return names

def commands_list():
	path = 'commands.txt'
	command_file = open(path, 'r')
	commands = command_file.read()
	command_file.close()
	return commands

def add_car(INVENTORY, new_car):
	exist = False
	for car in INVENTORY:
		if car == new_car:
			exist = True
			response = car + ' is already in car list'
			break
	if exist == False:
		INVENTORY[new_car] = None
		update_inventory(INVENTORY)
		response = 'Added car ' + new_car
	return response

def add_name(NAMES, new_name):
	exist = False
	for name in NAMES:
		if name == new_name:
			exist = True
			response = name + ' is already in names list'
			break
	if exist == False:
		NAMES.append(new_name)
		update_names(NAMES)
		response = 'Added name ' + new_name
	return response

def delete_car(INVENTORY, command):
	for car in INVENTORY:
		if command.startswith('delete car ' + car):
			del INVENTORY[car]
			update_inventory(INVENTORY)
			response = 'Deleted the ' + car + ' from the car list'
			break
		else:
			response = 'Do not have that car in inventory'
	return response

def delete_name(NAMES, command):
	for name in NAMES:
		if command.startswith('delete name ' + name):
			NAMES.remove(name)
			update_names(NAMES)
			response = 'Deleted name ' + name + ' from the name list'
			break
		else:
			response = 'I do not know that name'
	return response

def update_I(INVENTORY, NAMES, username, command):
	for name in NAMES:
		if name == username:
			for car in INVENTORY:
				if (command.startswith('I took the ' + car)) or (command.startswith('I have the ' + car)):
					INVENTORY[car] = username
					update_inventory(INVENTORY)
					response = 'Recorded ' + username + ' took the ' + car
					break
				else:
					response = 'That car is not in the car list'
			break
		else:
			response = 'I do not know you'
	return response

def return_carI(INVENTORY, NAMES, username, command):
	for name in NAMES:
		if name == username:
			for car in INVENTORY:
				if command.startswith('I returned the ' + car):
					if INVENTORY[car] == username:
						INVENTORY[car] = None
						update_inventory(INVENTORY)
						response = 'Recoreded ' + username + ' returned the ' + car
						break
					else:
						if len(INVENTORY[car]) == 0:
							response = 'You do not currenty have the ' + car + '. Nobody currently has the ' + car
						else:
							response = 'You do not currenty have the ' + car + '. ' + INVENTORY[car] + ' currently has the ' + car
					break
				else:
					response = 'That car is not in the car list'
			break
		else:
			response = 'I do not know you'
	return response

def return_car(INVENTORY, NAMES, command):
	for name in NAMES:
		if command.startswith(name + ' returned the'):
			for car in INVENTORY:
				if command.startswith(name + ' returned the ' + car):
					if INVENTORY[car] == name:
						INVENTORY[car] = None
						update_inventory(INVENTORY)
						response = 'Recorded ' + name + ' retuned the ' + car
						break
					else:
						if len(INVENTORY[car]) == 0:
							response = name + ' does not currently have the ' + car + '. Nobody currently has the ' + car
						else:
							response = name + ' does not currently have the ' +  car + '. ' + INVENTORY[car] + ' currently has the ' + car
					break
				else:
					response = 'That car is not in the list'
			break
		else:
			response = 'I do not know that person.'
	return response

def update_owner(INVENTORY, NAMES, command):
	for name in NAMES:
		if (command.startswith(name + ' has the')) or (command.startswith(name + ' took the')):
			for car in INVENTORY:
				if (command.startswith(name + ' has the ' + car)) or (command.startswith(name + ' took the ' + car)):
					INVENTORY[car] = name
					update_inventory(INVENTORY)
					response = 'Recorded ' + name + ' has the ' + car
					break
				else:
					response = 'Cannot find that car'
			break
		else:
			response = 'I do not know that name'
	return response

def find_car(INVENTORY, command):
	for car in INVENTORY:
		if (command.startswith('who has the ' + car)) or (command.startswith('where is the ' + car)):
			response = INVENTORY[car] + ' has the ' + car
			break
		else:
			response = 'That car is not on the car list'
	return response

def find_name(INVENTORY, NAMES, command):
	found = False
	for name in NAMES:
		if command.startswith('what does ' + name + ' have'):
			found = True
			response = name + ' has the following:'
			for car in INVENTORY:
				if INVENTORY[car] == name:
					response += ' ' + car
			break
	if found == False:
		response = 'I do not know that name'
	return response

def handle_messages(event):
	response = None

	INVENTORY = get_inventory()
	NAMES = get_names()
	user = slack_client.api_call('users.info', token = os.environ.get('SLACK_BOT_TOKEN'), user = event['user'])
	username = user['user']['profile']['display_name']
	message = event['text']

	# replace @user_id with username in message
	direct_mention = re.search(MENTION_REGEX, message)
	if direct_mention:
		message = at_user(direct_mention, message)

	# command list
	if message.startswith('commands list'):
		commands = commands_list()
		response = commands

	# car list
	elif message.startswith('car list'):
		inventory = car_list()
		response = inventory

	# name list
	elif (message.startswith('names list')) or (message.startswith('name list')):
		names = names_list()
		response = names

	# delete car
	elif message.startswith('delete car'):
		reply = delete_car(INVENTORY, message)
		response = reply

	# delete name
	elif message.startswith('delete name'):
		reply = delete_name(NAMES, message)
		response = reply

	# update inventory - checkout
	elif (message.startswith('I took')) or (message.startswith('I have')):
		reply = update_I(INVENTORY, NAMES, username, message)
		response = reply

	# update inventory - checkin
	elif message.startswith('I returned the'):
		reply = return_carI(INVENTORY, NAMES, username, message)
		response = reply

	# find car
	elif (message.startswith('who has the')) or (message.startswith('where is the ')):
		reply = find_car(INVENTORY, message)
		response = reply

	# find name
	elif re.match('what does [a-zA-Z]+.* have', message):
		reply = find_name(INVENTORY, NAMES, message)
		response = reply

	# update inventory - checkout
	elif (re.match('^[a-zA-Z]+.* has the', message)) or (re.match('^[a-zA-Z]+.* took the', message)):
		reply = update_owner(INVENTORY, NAMES, message)
		response = reply

	# update inventory - checkin
	elif re.match('^[a-zA-Z]+.* returned the', message):
		reply = return_car(INVENTORY, NAMES, message)
		response = reply

	# add name
	elif message.startswith('add name'):
		new_name = message[9:]
		reply = add_name(NAMES, new_name)
		response = reply

	# add car
	elif message.startswith('add car'):
		new_car = message[8:]
		reply = add_car(INVENTORY, new_car)
		response = reply

	# Sends the response back to the channel
	if response != None:
		slack_client.api_call(
			'chat.postMessage',
			channel = event['channel'],
			text = response
			)

def parse_bot_commands(slack_events):
	"""
		Parses a list of events coming from the Slack RTM API to find bot commands.
		If bot command found, this function returns a tuple of command and channel.
		If not found, then this function returns None, None.
	"""
	for event in slack_events:
		if event['type'] == 'message' and not 'subtype' in event:
			user_id, message = parse_direct_mention(event['text'])
			# print('@id', user_id)
			# print('message ', message)
			if user_id == starterbot_id:
				user = event['user']
				# return message, event['channel']
				return message, event
			else:
				handle_messages(event)
	return None, None

def parse_direct_mention(message_text):
	"""
		Finds a direct mention (a mention that is at the beginning) in message text and returns the user ID which was mentioned. If there is no direct mention, returns None.
	"""
	matches = re.search(MENTION_REGEX, message_text)
	#first group contains the username, second group contains remaining message
	return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_bot_command(command, channel, user):
	"""
		Executes bot command if the command is known
	"""
	INVENTORY = get_inventory()
	NAMES = get_names()
	user = slack_client.api_call('users.info', token = os.environ.get('SLACK_BOT_TOKEN'), user = user)
	USERNAME = user['user']['profile']['display_name']

	print('command = ', command)
	# replace @user_id with username in message
	direct_mention = re.search(MENTION_REGEX, command)
	if direct_mention:
		command = at_user(direct_mention, command)

	# Default response is help text for the user
	default_response = "Not sure what you mean. Try {} for a list of different commands".format(EXAMPLE_COMMAND)

	# Finds and executes the given command, filling in response
	response = None

	# list of all cars and who has them
	if command.startswith('car list'):
		inventory = car_list()
		response = inventory

	# list of all names
	elif (command.startswith('names list')) or (command.startswith('name list')):
		names =  names_list()
		response = names

	# find car
	elif (command.startswith('who has the')) or (command.startswith('where is the')):
		reply = find_car(INVENTORY, command)
		response = reply

	# find name
	elif re.match('what does [a-zA-Z]+.* have', command):
		reply = find_name(INVENTORY, NAMES, command)
		response = reply

	# update INVENTORY
	elif (command.startswith('I have')) or (command.startswith('I took')):
		reply = update_I(INVENTORY, NAMES, USERNAME, command)
		response = reply

	# update inventory - checkin
	elif command.startswith('I returned'):
		reply = return_carI(INVENTORY, NAMES, USERNAME, command)
		response = reply

	# update INVENTORY
	elif(re.match('^[a-zA-Z]+.* has the', command)) or (re.match('^[a-zA-Z]+.* took the', command)):
		reply = update_owner(INVENTORY, NAMES, command)
		response = reply

	# update inventory - checkin
	elif re.match('^[a-zA-Z]+.* returned the', command):
		reply = return_car(INVENTORY, NAMES, command)
		response = reply

	# add name
	elif command.startswith('add name'):
		new_name = command[9:]
		reply = add_name(NAMES, new_name)
		response = reply

	# add car
	elif command.startswith('add car'):
		new_car = command[8:]
		reply = add_car(INVENTORY, new_car)
		response = reply

	# delete car
	elif command.startswith('delete car'):
		reply = delete_car(INVENTORY, command)
		response = reply
	
	# delete name
	elif command.startswith('delete name'):
		reply = delete_name(NAMES, command)
		response = reply

	# command list
	elif command.startswith('commands list'):
		commands = commands_list()
		response = commands

	# Sends the response back to the channel
	slack_client.api_call(
		'chat.postMessage',
		channel = channel,
		text = response or default_response
		)

if __name__ == '__main__':
	if slack_client.rtm_connect(with_team_state=False):
		print('Starter Bot connected and running')
		# Read bot's user ID by calling Web API method 'auth.test'
		starterbot_id = slack_client.api_call('auth.test')['user_id']
		while True:
			command, event = parse_bot_commands(slack_client.rtm_read())
			if command:
				channel = event['channel']
				user = event['user']
				handle_bot_command(command, channel, user)
			time.sleep(RTM_READ_DELAY)
	else:
		print('Connection failed. Exception traceback printed above.')