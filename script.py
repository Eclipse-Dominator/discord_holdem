import discord
import numpy as np
import asyncio
import subprocess
from shlex import split

TOKEN = '#token' #token

class GrLogic(object):
	"""docstring for grLogic"""
	"""
	playerX = {
		"name": "xxx"
		"pid": "xxx"
		"bank": 0
	}
	"""
	def __init__(self):
		super(GrLogic, self).__init__()
		self.suites = [":spades:",":hearts:",":diamonds:",":clubs:"]
		self.cards = [":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":keycap_ten:" ,":regional_indicator_j:",":regional_indicator_q:",":regional_indicator_k:",":a:"]
		self.players = []
		self.gr_round = []
		self.pot = 0
		self.deck = []
		self.displayedCards = []
		self.modID = ""
		self.turnIndex = 0
		self.part_no = -1     # 0 - preflop bet, 1 - Flop bet, 2 - turn round, 3 - river round, 4 - showdown
		self.shuffleDeck()
		self.minimumBet = 4
		self.raisedAmount = self.minimumBet
		self.smallBlindID = -1
		self.msgBuffer = []
		self.msgPrivateBuffer = []
		self.roundNo = 0
		print("poker init")

	def create_host_room(self,pid,name):
		if self.modID == "":
			self.modID = pid
			pTemp = {
				"name": name,
				"pid": pid,
				"bank": 100,
				"broke": False,
				"completed": False,
				"fold": False,
				"cards": [],
				"moneyAdded": 0,
				"strength": []
			}
			self.players.append(pTemp)
			print("room created")
			return True,"has created a game of Texas Hold'em, type t/join to join!"
		return True,"a room is already created!"

	def gr_add_player(self,pid,name):
		if self.part_no != -1:
			return True, "The game has already started"
		if self.modID == "":
			return True, ",no room has been created. Type t/init to create one!"
		for player in self.players:
			if player["pid"] == pid:
				return True, "already in the room"

		pTemp = {
			"name": name,
			"pid": pid,
			"bank": 100,
			"broke": False,
			"completed": False,
			"fold": False,
			"cards": [],
			"moneyAdded": 0,
			"strength": []
		}
		self.players.append(pTemp)
		print("{} added".format(name))
		return True, "added!"

	def addPot(self,pid,amount):
		for i in range(len(self.players)):
			if self.players[i]["pid"] == pid:
				if self.players[i]["fold"]:
					self.msgBuffer.append("You have already folded!")
					return False
				elif self.players[i]["bank"] == 0:
					self.msgBuffer.append("You are suffering from poverty!")
					return False
				else:
					pBank = self.players[i]["bank"]
					if pBank <= amount: 				#all in
						self.players[i]["bank"] = 0
						self.pot += pBank
						self.players[i]["broke"] = True
						self.players[i]["moneyAdded"] += pBank
						self.msgBuffer.append("{} Goes ALL IN!".format(self.players[i]["name"]))
						return True
					else: 								# add some to pot
						self.players[i]["bank"] -= amount
						self.pot += amount
						self.players[i]["moneyAdded"] += amount
						self.msgBuffer.append("{} added ${} to the pot".format(self.players[i]["name"],amount))
						return True
		self.msgBuffer.append("You are not in the game!")
		return False

	def round_completion_reset(self):		 # set all player to incomplete
		self.smallBlindID = ""
		self.raisedAmount = 0
		for player in self.players:           
			player["moneyAdded"] = 0
			if player["fold"] or player["broke"]:
				if self.part_no == 0:
					player["fold"] = True
				player["completed"] = True
			else:
				player["completed"] = False
		if sum(x["fold"] or x["broke"] for x in self.players) == len(self.players) - 1:
			for player in self.players:
				player["completed"] = True

		return
	def round_raise_reset(self):
		for player in self.players:
			if player["fold"] or player["broke"]:
				player["completed"] = True
			else:
				player["completed"] = False
	def gs_start(self,pid):
		if pid != self.modID:
			return True,"you are not the game host"
		elif self.part_no != -1:
			return True,": Game has already begun"
		return self.gs_next()
	def gs_next(self):
		self.part_no += 1
		self.round_completion_reset()
		if self.turnIndex == len(self.players):
			self.turnIndex = 0
		if self.part_no == 0:		# preflop Bet
			self.turnIndex = 0
			self.smallBlindID = -1
			self.bigBlindID = -1
			self.raisedAmount = self.minimumBet * ( (3 + self.roundNo) // 3 )
			for player in self.players:
				if player["completed"] == False:
					player["cards"] = []
					player["cards"].append(self.drawCard())
					player["cards"].append(self.drawCard())
					self.msgPrivateBuffer.append([player["pid"],"```css\nYour Cards:```"])
					self.msgPrivateBuffer.append("{}\n{}".format(player["cards"][0],player["cards"][1]))
			for player in self.players:
				if player["completed"] == False:
					if self.smallBlindID == -1:
						self.addPot(player["pid"],self.raisedAmount/2)
						self.smallBlindID = player["pid"]
						print("small blind by {}".format(player["pid"]))
						self.msgBuffer.append("@{} pays a small blind of ${}".format(player["name"],self.raisedAmount/2.0))
					else:
						self.addPot(player["pid"],self.raisedAmount)
						self.turnIndex = (self.players.index(player) + 1)%len(self.players)
						print("big blind by {}".format(player["pid"]))
						self.msgBuffer.append("@{} pays a big blind of ${}".format(player["name"],self.raisedAmount/1.0))
						break
			return False,self.nextTurn()

		elif self.part_no == 1:		# flop bet
			self.displayedCards.append(self.drawCard())
			self.displayedCards.append(self.drawCard())
			self.displayedCards.append(self.drawCard())
			self.msgBuffer.append("----------\n```css\nNow for the flop:\n```")
			self.msgBuffer.append("\n".join(self.displayedCards))
			self.msgBuffer.append("----------")
			return False,self.nextTurn()
		
		elif self.part_no == 2:		# turn bet
			self.displayedCards.append(self.drawCard())
			self.msgBuffer.append("----------\n```css\nNow for the turn:\n```")
			self.msgBuffer.append("\n".join(self.displayedCards))
			self.msgBuffer.append("----------")
			return False,self.nextTurn()
		elif self.part_no == 3:		# river bet
			self.displayedCards.append(self.drawCard())
			self.msgBuffer.append("----------\n```css\nNow for the river:\n```")
			self.msgBuffer.append("\n".join(self.displayedCards))
			self.msgBuffer.append("----------")
			return False,self.nextTurn()
		else:						# showdown
			self.msgBuffer.append("----------\n```css\nShowdown:\n```")
			self.msgBuffer.append("\n".join(self.displayedCards))
			self.msgBuffer.append("----------")
			return False,self.endGame()

	def call(self,pid,check=0):
		if self.players[self.turnIndex]["pid"] != pid:
			return True, "```css\nIt is not your turn yet\n```"
		if check == 0:
			self.msgBuffer.append("```css\n@{} Called\n```".format(self.players[self.turnIndex]["name"]))
			if self.raisedAmount-self.players[self.turnIndex]["moneyAdded"] > 0:
				self.addPot(pid,self.raisedAmount-self.players[self.turnIndex]["moneyAdded"])
			self.players[self.turnIndex]["completed"] = True
			self.turnIndex = (self.turnIndex + 1)%len(self.players)
			return False,self.nextTurn()
		else:
			if check > self.players[self.turnIndex]["bank"]:
				check = self.players[self.turnIndex]["bank"]
				self.msgBuffer.append("You don't have that much money, changing raise to all in! :P")
			if self.smallBlindID == self.players[self.turnIndex]["pid"]:
				self.raisedAmount = self.raisedAmount/2 + check
			else:
				self.raisedAmount += check
			self.addPot(pid,self.raisedAmount-self.players[self.turnIndex]["moneyAdded"])
			self.msgBuffer.append("```css\n@{} has raised bet to ${}\n```".format(self.players[self.turnIndex]["name"],self.raisedAmount))
			self.round_raise_reset()
			self.players[self.turnIndex]["completed"] = True
			return False,self.nextTurn()

	def fold(self,pid):
		if self.part_no == -1:
			return True, "u can't fold now"
		if self.players[self.turnIndex]["pid"] != pid:
			return True, "```css\nIt is not your turn yet\n```"
		self.players[self.turnIndex]["fold"] = True
		self.players[self.turnIndex]["completed"] = True
		self.msgBuffer.append("{} has folded!".format(self.players[self.turnIndex]["name"]))
		return False,self.nextTurn()

	def endGame(self):
		playersLeft = list(filter(lambda x: x["fold"] == False,self.players))
		print(playersLeft)
		if len(playersLeft) == 1 and False:
			print("only 1 player left")
			self.msgBuffer.append("{} wins ${}!".format(playersLeft[0]["name"],self.pot))
			playersLeft[0]["bank"] += self.pot
			self.pot = 0
		else:
			print("Judging")
			for player in self.players:
				if not player["fold"]:
					player["cards"] += self.displayedCards
					print(player["cards"])
					player["strength"],unconverted = self.evaluateHand(player["cards"])
					converted = []
					for ucard in unconverted:
						converted.append("{} {}".format(self.cards[ucard[0]],self.suites[ucard[1]]))
					print(player["strength"],player["cards"])
					self.msgBuffer.append("```css\n{} SCORE: {} Cards:\n```".format(player["name"],", ".join([str(a) for a in player["strength"]])))
					self.msgBuffer.append("{}".format(" :white_small_square:  ".join(converted)))
				else:
					msg = "```css\n{} has folded!\n```".format(player["name"])
					print(msg)
					self.msgBuffer.append(msg)
			playerTemp = list(filter(lambda x: x["fold"] == False,self.players))[:]
			
			addTuple = lambda a,b: tuple(list(a) + [b])
			playerTemp.sort(key = lambda x: x["strength"],reverse=True)
			playerWinner = []
			winningPattern = playerTemp[0]["strength"]
			for player in playerTemp:
				if player["strength"] == winningPattern:
					playerWinner.append(player)
				else: break

			splitNum = len(playerWinner)
			moneyGiven = self.pot // splitNum
			for winner in playerWinner:
				self.msgBuffer.append("```css\n{} won ${}!\n```".format(winner["name"],moneyGiven))
				winner["bank"] += moneyGiven
				self.pot -= moneyGiven

		if self.newRound():
			self.msgBuffer.append("```css\nStarting next round\n```")
			self.roundNo += 1
			return False,self.gs_next()
		print("game ends")
		return True, "Closing Game Room!"

	def printBank(self):
		self.msgBuffer.append("```css\nPOT:${}\n```-------\n".format(self.pot))
		for player in self.players:
			self.msgBuffer.append("```css\nName: {}, Bank: {}, Fold: {}\n```".format(player["name"],player["bank"],player["fold"]))
		return True, "Done"


	def evaluateHand(self,hand):
		addTuple = lambda a,b: tuple(list(a)+list(b))
		temp = []
		print(hand)
		for card in hand:
			tempC = card.split(" ")
			numIndex = self.cards.index(tempC[0])
			suiteIndex = self.suites.index(tempC[1])
			temp.append([numIndex,suiteIndex])
		temp.sort(key=lambda x:x[0])
		#detect straight flush
		check,hand = self.detect_straight_flush(temp)
		if check:
			highC,card = self.high_card(hand)
			if highC == 12:
				return (10) #royal
			return addTuple([9],highC),hand #straight flush
		check,hand = self.numDetection(temp,[4]) # four of a kind
		if check: 
			for card in hand[0]:
				temp.remove(card)
			highC,card = self.high_card(temp)
			return addTuple([8],highC),hand[0]+card

		check,hand = self.numDetection(temp,[3,2]) # full house
		if check:
			return (7,hand[0][0][0],hand[1][0][0]),hand[0]+hand[1]
		
		check,hand = self.detect_flush(temp) # flush
		if check:
			highC,card = self.high_card(hand)
			return addTuple([6],highC),hand

		check,hand = self.detect_straight(temp) # straight
		if check:
			highC,card = self.high_card(hand)
			return (5,highC),hand
		print("card: ",temp)
		check,hand = self.numDetection(temp,[3]) # three of a kind
		if check: 
			threeKind = hand[0][0][0]
			for card in hand[0]:
				temp.remove(card)
			highC1,card1 = self.high_card(temp,num=2)
			return addTuple((4,threeKind),highC1),hand[0]+card1


		check,hand = self.numDetection(temp,[2,2]) # two pair
		if check: 
			for card in hand[0]:
				temp.remove(card)
			for card in hand[1]:
				temp.remove(card)
			highC,cards = self.high_card(temp)
			return addTuple((3,hand[0][0][0],hand[1][0][0]),highC),hand[0]+hand[1]+cards

		check,hand = self.numDetection(temp,[2]) # pair
		if check: 
			for card in hand[0]:
				temp.remove(card)
			highC, cards = self.high_card(temp,num=3)
			return addTuple((2,hand[0][0][0]),highC),hand[0]+cards
		print("card: ",temp)
		highC,card = self.high_card(temp,num=5)
		return addTuple([1],highC),card

	
	def numDetection(self,hands,patternArr): #[4] -four of a kind, [3,2] -full house, [3] - three of a kind, [2,2] - 2 pair, [2] - pair
		hands.sort(key=lambda x:x[0],reverse=True)
		hand = hands[:]
		print("hands",hand)
		numCount = [0]*13
		for card in hand:
			numCount[card[0]] += 1
		numCount.reverse()
		handT = []
		for pattern in patternArr:
			if not pattern in numCount:
				return False, None
			else:
				cardNo = 12 - numCount.index(pattern)
				handT.append([x for x in hand if x[0] == cardNo])
				hand = list(filter(lambda x: x[0] != cardNo,hand))
				numCount[12-cardNo] = 0
				print("hands",hand)
		print("handT:",handT)
		return True, handT


	def high_card(self,hand,num=1):
		print("temp: ",hand)
		hand.sort(key=lambda x:x[0],reverse=True)
		sizeList = []
		cardList = []
		for i in range(num):
			sizeList.append(hand[i][0])
			cardList.append(hand[i])
		print(tuple(sizeList),cardList)
		return tuple(sizeList),cardList

	def detect_straight_flush(self,hand):
		hand.sort(key=lambda x:x[0])
		#detect straight flush
		suitecount = [0,0,0,0] #spade heart diamond club
		maxSuiteIndex = suitecount.index(max(suitecount))
		flush_state,handT = self.detect_flush(hand)
		if flush_state:
			straight_state,handT = self.detect_straight(handT)
			if straight_state:
				return True,handT
		return False,None

	def detect_flush(self,hand):
		suitecount = [0,0,0,0] #spade heart diamond club
		for card in hand:
			suitecount[card[1]] += 1
		maxSuiteIndex = suitecount.index(max(suitecount))
		handT = []
		if suitecount[maxSuiteIndex] < 5:
			return False,None
		else:
			for card in hand:
				if card[1] == maxSuiteIndex:
					handT.append(card)
			return True, handT

	def detect_straight(self,hand):
		hand.sort(key=lambda x:x[0])
		if len(hand) < 5:
			return False,None
		straight = hand[0][0]
		count = 1
		start_index=0
		end_index=0
		for card in hand[1:]:
			if card[0] == straight + 1:
				straight = card[0]
				count += 1
				end_index = hand.index(card)
			else:
				straight = card[0]
				count = 1
				end_index = hand.index(card)
				start_index = hand.index(card)
		if count < 5:
			return False,None
		else:
			return True, hand[start_index:end_index+1]

	
	def newRound(self):
		self.displayedCards = []
		for player in self.players:
			player["hand"] = []
			player["completed"] = False
			player["fold"] = False
			if player["bank"] > 0:
				player["broke"] = False
			else:
				player["broke"] = True
				player["fold"] = True
				player["completed"] = True
		playersLeft = list(filter(lambda x: x["fold"] == False,self.players))
		if len(playersLeft) == 1:
			self.msgBuffer.append("```css\nPlayer {} has won the game!\n```".format(playersLeft[0]["name"]))
			tempBuffer = self.msgBuffer[:]
			self.__init__()
			self.msgBuffer = tempBuffer[:]
			return False
		self.part_no = -1
		self.players.append(self.players.pop(0))
		self.shuffleDeck()
		return True
			
	def clearBuffer(self):
		self.msgBuffer = []
		return

	def clearPBuffer(self):
		self.msgPrivateBuffer = []
		return

	def nextTurn(self):
		if sum(player["fold"]==False for player in self.players) == 1:
			#return False,self.endGame()
			return False,self.gs_next()
		elif all(player["completed"] for player in self.players):
			return False,self.gs_next()
		if self.players[self.turnIndex]["completed"]:
			self.turnIndex += 1
			if self.turnIndex == len(self.players):
				self.turnIndex = 0
			return self.nextTurn()
		return True, "```css\n@{}, it is your turn now!\n```".format(self.players[self.turnIndex]["name"])		

	def drawCard(self):
		return self.deck.pop()

	def shuffleDeck(self):
		self.deck = []
		for suite in self.suites:
			for card in self.cards:
				self.deck.append("{} {}".format(card,suite))
		for i in range(np.random.randint(10,50)):
			np.random.shuffle(self.deck)
		print("duplicate:")
		print(len(self.deck) - len(set(self.deck)))
		return 1

class MyClient(discord.Client):
	def __init__(self, *args, **kwargs):
	    super().__init__(*args, **kwargs)   #def                #Function           parameter
	                                        #self.dm            #direct message     uid/userObj, msg content
	                                        #self.cm            #channel message    cid/channelObj, msg content
	                                        #self.delm          #delete message     msg object
	    self.cid = "#cid"
	    self.gr = GrLogic()


	def startBGtask(self):
	    self.loop.create_task(self.my_background_task())        # create the background task and run it in the background

	async def my_background_task(self):
	    await self.wait_until_ready()
	    
	    while not self.is_closed:
	        #rerun loop
	        await asyncio.sleep(10) # task runs every 60 seconds

	async def on_ready(self):
	    print('Logged in as')
	    print(self.user.name)
	    print(self.user.id)
	    print("----------------")
	    self.cm(self.cid,"I'm now online")

	async def on_message(self,message):
	    if message.author == self.user and message.channel.id == self.cid:
	        return
	    self.cmdSwitch(message)
	    return

	def help(self,msgObj):
		msg = "{0.author.mention}, welcome to the Texas Hold'em Bot!\nType t/help to display this message\nType t/init to create a game room\nType t/join to join available game room\nType t/start to start the game!\nType t/check or t/call to check or call respectively\nType t/raise <amount> to raise\nType t/banks to view current financial data\nType t/reboot to close the room.".format(msgObj)
		self.cm(self.cid,msg)

	def displayBuffer(self):
		print(self.gr.msgBuffer)
		if self.gr.msgBuffer == "":
			return
		for buffertxt in self.gr.msgBuffer:
			self.cm(self.cid,buffertxt)			
		self.gr.clearBuffer()
		return

	def displayPrivateBuffer(self):
		if self.gr.msgPrivateBuffer == "":
			return
		for msg in self.gr.msgPrivateBuffer:
			if msg[0] == "" or msg[1] == "":
				pass
			self.dm(msg[0],msg[1])
		self.gr.clearPBuffer()
		return

	def gr_init(self,msgObj):
		msg = self.analyseOutput(self.gr.create_host_room(msgObj.author.id,msgObj.author))
		self.displayPrivateBuffer()
		self.displayBuffer()
		self.cm(self.cid,"{0.author.mention} {1}".format(msgObj,msg))
		return

	def gr_join(self,msgObj):
		msg = self.analyseOutput(self.gr.gr_add_player(msgObj.author.id,msgObj.author))
		self.displayPrivateBuffer()
		self.displayBuffer()
		self.cm(self.cid,"{0.author.mention} {1}".format(msgObj,msg))
		return

	def gr_start(self,msgObj):
		msg = self.analyseOutput(self.gr.gs_start(msgObj.author.id))
		self.displayPrivateBuffer()
		self.displayBuffer()
		self.cm(self.cid,"{0}".format(msg))
		return

	def gr_call(self,msgObj):
		msg = self.analyseOutput(self.gr.call(msgObj.author.id))
		self.displayPrivateBuffer()
		self.displayBuffer()
		self.cm(self.cid,"{0}".format(msg))
		return

	def gr_raise(self,msgObj):
		pid = msgObj.author.id
		content = msgObj.content.split(" ")[1]
		raisedAmount = 0
		try:
			raisedAmount = int(content)
		except Exception as e:
			self.cm(self.cid,"```css\nAn error occured while processing {}\n```".format(content))
			return
		msg = self.analyseOutput(self.gr.call(msgObj.author.id,raisedAmount))
		self.displayPrivateBuffer()
		self.displayBuffer()
		self.cm(self.cid,"{0}".format(msg))
		return

	def gr_fold(self,msgObj):
		msg = self.analyseOutput(self.gr.fold(msgObj.author.id))
		self.displayPrivateBuffer()
		self.displayBuffer()
		self.cm(self.cid,"{0}".format(msg))

	def gr_bank(self,msgObj):
		msg = self.analyseOutput(self.gr.printBank())
		self.displayPrivateBuffer()
		self.displayBuffer()
		self.cm(self.cid,"{0}".format(msg))

	def gr_exit(self,msgObj):
		print(msgObj.author.id)
		if msgObj.author.id == self.gr.modID or msgObj.author.id == "#admin id":
			self.gr.__init__()
			self.cm(self.cid,"Quitting room")
			return
		self.cm(self.cid,"You do not have the permission to close this room")	
		return

	def cmdSwitch(self,msgObj):
		header="t/"
		content = msgObj.content.split(" ")[0]
		switcher = {
			header+"help": self.help,
			header+"init": self.gr_init,
			header+"join": self.gr_join,
			header+"start": self.gr_start,
			header+"call": self.gr_call,
			header+"check": self.gr_call,
			header+"raise": self.gr_raise,
			header+"fold": self.gr_fold,
			header+"banks": self.gr_bank,
			header+"reboot": self.gr_exit
		}
		func = switcher.get(content,lambda x:"default")
		func(msgObj)
		return

	def analyseOutput(self,inputArr):
		if inputArr[0]:
			return inputArr[1]
		return self.analyseOutput(inputArr[1])

	def cm(self,cid,msg):
		self.loop.create_task(self.sendChannelMsg(cid,msg))

	def dm(self,pid,msg):
		self.loop.create_task(self.sendUserMsg(pid,msg))

	def delM(self,msgObj):
		self.loop.create_task(self.deleteUserMsg(msgObj))

	async def sendUserMsg(self,cid,msg):
		await self.send_message(await client.get_user_info(cid),msg)
		return

	async def sendChannelMsg(self,cid,msg):
		await self.send_message(discord.Object(id=cid),msg)
		return
	async def deleteUserMsg(self,msg):
		await self.delete_message(msg)
		return

client = MyClient()
client.run(TOKEN)