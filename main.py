#coding:utf-8

import os
import sys
import time
import json

import telegram
from telegram.ext import Dispatcher,Handler

from flask import Flask,request,Response
from werkzeug.utils import secure_filename

import logging

logging.basicConfig(level=logging.INFO,format="[%(asctime)s][%(levelname)s][%(thread)d][%(filename)s:%(lineno)d]%(message)s")

loggerList = []
loggerSub = logging.getLogger("Sub")
logger = logging.getLogger(__name__)
loggerList.append(loggerSub)
loggerList.append(logger)

formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(thread)d][%(filename)s:%(lineno)d]%(message)s")
fileHandler = logging.FileHandler(time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + ".log",encoding="utf-8")
fileHandler.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

logLevel = logging.DEBUG

for ll in loggerList:
	ll.setLevel(logLevel)
	ll.addHandler(consoleHandler)
	ll.addHandler(fileHandler)

from config import config

app = Flask(__name__)
bot = telegram.Bot(token=config["telegram"]["token"])
bot.set_webhook(config["telegram"]["webhookAddress"])

@app.route("/botHook",methods=["POST"])
def botHookHandler():
	if (request.method == "POST"):
		logger.info(request.get_json(force=True))
		update = telegram.update.Update.de_json(request.get_json(force=True),bot)
		processUpdate(update)
	return "ok"

@app.route("/UploadResult",methods=["POST"])
def uploadResult():
	allowedExts = ["png"]
	uploadFolder = config["ssrSpeed"]["uploadDir"]
	if (request.method == "POST"):
		filename = ""
	#	print(request.files)
		if (request.form.get("token",type=str,default="") != config["ssrSpeed"]["token"]):
			return Response(status=401)
		if ("file" in request.files):
			_file = request.files["file"]
			if (_file.filename == ""):
				return "Invalid File"
			filename = _file.filename
			if(_file and ('.' in filename and filename.rsplit(".",1)[1].lower() in allowedExts)):
				filename = secure_filename(_file.filename)
				logger.info("Saving file %s" % filename)
				filename = os.path.join(uploadFolder,filename)
				_file.save(filename)
				logger.info("File saved as %s" % filename)
		remark = request.form.get("remark",type=str,default="")
		sendResult(filename,remark)
	return "ok"

def sendResult(filename,remark):
	telegramConfig = config["telegram"]
	for chatId in telegramConfig["chatId"]:
		bot.send_message(chat_id=chatId,text=remark)
		iid = bot.send_message(chat_id=chatId,text="Sending file...").message_id
		bot.send_document(chat_id=chatId,document=open(filename,"rb"))
		bot.delete_message(chat_id=chatId,message_id=iid)

def processUpdate(update):
	if (update.message.text == "/getChatId"):
		getChatIdHandler(bot,update)

def getChatIdHandler(bot,update):
	bot.send_message(chat_id=update.message.chat_id,text=update.message.chat_id)
	

if (__name__ == "__main__"):
	flaskConfig = config["flask"]
	app.run(host=flaskConfig["host"],port=flaskConfig["port"],debug=flaskConfig["debug"])

