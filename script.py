import discord
import asyncio
import subprocess
from shlex import split
import time
from GrLogic import GrLogic

TOKEN = ""
with open("token",'r') as rF:
	TOKEN = rF.readline()
	
assert TOKEN != "","No Token detected"

class MyClient(discord.Client):
	def __init__(self, *args, **kwargs):
	    super().__init__(*args, **kwargs)   #def                #Function           parameter
	                                        #self.dm            #direct message     uid/userObj, msg content
	                                        #self.cm            #channel message    cid/channelObj, msg content
	                                        #self.delm          #delete message     msg object
	    self.cid = []
	    self.roomNo = 1
	    


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
		self.channelID = []

	async def on_message(self,message):
		cids = [x["channel"].id for x in self.cid]
		if message.author == self.user:
			return
		if message.channel.id in cids:
			cid = cids.index(message.channel.id)
			self.gameSwitch(message,self.cid[cid])
			return
		self.cmdSwitch(message)
		return

	def help(self,msgObj,a=None):
		msg = "{0.author.mention}\n```css\nWhen inside the game room, type /+\nhelp: display this message\njoin: join this room as a player\nstart: start the game if you are the mod\nexit: leave the current room\ncards: display the cards currently revealed\nclose: Close the current room (only for mods and admins)\ncall, check, fold: do as it says\nraise <xxx>: raise current bet by $xxx\nbanks: display current bank information\n```\n```css\nFor commands outside of game room. type t/\nroom: create a game room with you as the moderator of the room\nhelp: display this message\n```".format(msgObj)
		self.cm(msgObj.channel.id,msg)
		self.delM(msgObj)

	def displayBuffer(self,cid,gr):
		print(gr.msgBuffer)
		if gr.msgBuffer == "":
			return
		for buffertxt in gr.msgBuffer:
			self.cm(cid,buffertxt)			
		gr.clearBuffer()
		return

	def displayPrivateBuffer(self,channel,gr):
		if len(gr.msgPrivateBuffer) == 0:
			return
		temp = ""
		for msg in gr.msgPrivateBuffer:
			print(msg)
			if msg[0] == "" or msg[1] == "":
				continue
			if temp != msg[0]:
				temp = msg[0]
				self.dm(msg[0],"from {0.mention}".format(channel))
			self.dm(msg[0],msg[1])
		gr.clearPBuffer()
		return

	def create_game_room(self,msgObj):
		self.cm(msgObj.channel.id,"{0.author.mention} Creating room...".format(msgObj))
		self.newC(msgObj,"holdem-room-{}".format(self.roomNo))
		self.roomNo += 1
		return

	def gr_join(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		msg = self.analyseOutput(gr.gr_add_player(msgObj.author.id,msgObj.author))
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		self.cm(msgObj.channel.id,"{0.author.mention} {1}".format(msgObj,msg))
		return

	def gr_start(self,msgObj,cid):
		gr = cid["gr"]
		gr.closeStatus = False
		channelId = cid["channel"].id
		msg = self.analyseOutput(gr.gs_start(msgObj.author.id))
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		print(msg)
		self.cm(msgObj.channel.id,"{0}".format(msg))
		return

	def gr_call(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		msg = self.analyseOutput(gr.call(msgObj.author.id))
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		self.cm(msgObj.channel.id,"{0}".format(msg))
		return

	def gr_raise(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		pid = msgObj.author.id
		content = msgObj.content.split(" ")[1]
		raisedAmount = 0
		try:
			raisedAmount = int(content)
		except Exception as e:
			self.cm(self.cid,"```css\nAn error occured while processing {}\n```".format(content))
			return
		msg = self.analyseOutput(gr.call(msgObj.author.id,raisedAmount))
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		self.cm(msgObj.channel.id,"{0}".format(msg))
		return

	def gr_fold(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		msg = self.analyseOutput(gr.fold(msgObj.author.id))
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		self.cm(msgObj.channel.id,"{0}".format(msg))

	def gr_bank(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		msg = self.analyseOutput(gr.printBank())
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		self.cm(msgObj.channel.id,"{0}".format(msg))

	def gr_exit(self,msgObj,cid):
		gr = cid["gr"]
		if msgObj.author.id == gr.modID or msgObj.author.id == "451712069956534282":
			self.loop.create_task(self.deleteChannelAfterTime(cid["channel"],5))
			return
		self.cm(msgObj.channel.id,"You do not have the permission to close this room")	
		return

	def gr_cancel(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		if msgObj.author.id == gr.modID or msgObj.author.id == "451712069956534282":
			gr.closeStatus = False
			return
		self.cm(msgObj.channel.id,"You do not have the permission to cancel this process")	
		return

	def gr_leave(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		print("leave")
		msg = self.analyseOutput(gr.gr_leaveRoom(msgObj.author.id))
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		self.cm(msgObj.channel.id,"{0}".format(msg))
		return

	def gr_displaycards(self,msgObj,cid):
		gr = cid["gr"]
		channelId = cid["channel"].id
		print("leave")
		msg = self.analyseOutput(gr.displayCards())
		self.displayBuffer(channelId,gr)
		self.displayPrivateBuffer(cid["channel"],gr)
		self.cm(msgObj.channel.id,"{0}".format(msg))
		return


	def gameSwitch(self,msgObj,cid):
		header="/"
		content = msgObj.content.split(" ")[0]
		switcher = {
			header+"help": self.help,
			header+"join": self.gr_join,
			header+"start": self.gr_start,
			header+"call": self.gr_call,
			header+"check": self.gr_call,
			header+"raise": self.gr_raise,
			header+"fold": self.gr_fold,
			header+"banks": self.gr_bank,
			header+"close": self.gr_exit,
			header+"cancel": self.gr_cancel,
			header+"exit": self.gr_leave,
			header+"leave": self.gr_leave,
			header+"cards": self.gr_displaycards
		}
		func = switcher.get(content,lambda x,y:"default")
		func(msgObj,cid)
		return

	def cmdSwitch(self,msgObj):
		header="t/"
		content = msgObj.content.split(" ")[0]
		switcher = {
			header+"help": self.help,
			header+"room": self.create_game_room
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

	def newC(self,msgObj,name):
		task = self.loop.create_task(self.createNewRoom(msgObj,name))

	async def sendUserMsg(self,cid,msg):
		person = await self.get_user_info(cid)
		await self.send_typing(person)
		return await self.send_message(person,msg)

	async def sendChannelMsg(self,cid,msg):
		channel = discord.Object(id=cid)
		await self.send_typing(channel)
		return await self.send_message(channel,msg)

	async def deleteUserMsg(self,msg):
		await self.delete_message(msg)
		return

	async def createNewRoom(self,msgObj,cName):
		tempChannel = await self.create_channel(msgObj.channel.server,cName,type=discord.ChannelType.text)
		gr = GrLogic()
		self.cid.append({'channel':tempChannel,'gr':gr})
		msg = self.analyseOutput(gr.create_host_room(msgObj.author.id,msgObj.author))
		await self.sendChannelMsg(tempChannel.id,"{0.author.mention} {1}".format(msgObj,msg))
		self.loop.create_task(self.channelDeleteLoop(gr,tempChannel))
		return

	async def deleteChannelAfterTime(self,channel,closeTime):
		await self.sendChannelMsg(channel.id,"```css\nDeleting Channel in {}s...\n```".format(closeTime))
		await asyncio.sleep(closeTime)
		print("deleting channel")
		for cid in self.cid:
			if cid["channel"].id == channel.id:
				del cid["gr"]
				self.cid.remove(cid)
				break
		await self.delete_channel(channel)

	async def alertPlayer(self,pid,gr_cid,gr,timer):
		print("loop started")
		char = await self.get_user_info(pid)
		await asyncio.sleep(timer)
		await self.sendChannelMsg(gr_cid,"{0.mention}, please make your decision in 10 sec".format(char))
		await asyncio.sleep(10)
		await self.sendChannelMsg(gr_cid,"Skipping {0.mention}'s turn".format(char))
		msg = self.analyseOutput(gr.fold(pid))
		self.displayBuffer(gr_cid,gr)
		self.displayPrivateBuffer(gr_cid,gr)
		self.cm(gr_cid,"{0}".format(msg))



	async def channelDeleteLoop(self,gr,channel):
		print("loop started")
		task = None
		task2 = None
		currentTurn =  gr.turnIndex
		waitPlayerID = gr.players[currentTurn]["pid"]
		while channel.id in [x["channel"].id for x in self.cid]:
			if gr.closeStatus:
				if task == None:
					print("closing")
					task = self.loop.create_task(self.deleteChannelAfterTime(channel,120))
				if task2 != None:
					task2.cancel()
					task2 = None
			elif task != None:
				task.cancel()
				await self.sendChannelMsg(channel.id,"Closing Cancelled!")
				task = None
			if gr.part_no > -1 and not gr.closeStatus:
				if gr.turnIndex == currentTurn:
					if task2 ==None:
						print("cd start")
						task2 = self.loop.create_task(self.alertPlayer(waitPlayerID,channel.id,gr,90))
				else:
					if task2 != None:
						task2.cancel()
						task2 = None
					currentTurn = gr.turnIndex
					waitPlayerID = gr.players[currentTurn]["pid"]
			await asyncio.sleep(3)
		print("channel deleted")
		return 

client = MyClient()
client.run(TOKEN)
