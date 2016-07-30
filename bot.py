import requests
import time
import random
import sys
import re
import configparser
import codecs
from bs4 import BeautifulSoup

DATA = {'bot': [], 'users': [{}, ]}

class bot():

	def __init__(self):
		loadacc()
		self.time = int(time.time())
		self.acc = DATA 
		self.chat = int(self.acc['bot']['chat'])
		self.headers = {   'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0',
					       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					       'Connection': 'keep-alive',
					       'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'}
		self.help = '''Справка по командам:

		Статус - статус бота.
		N статус - статус N аккаунта.
		N Вход/Войти - войти в N аккаунт.
		N профиль - информация о N профиле.
		N в шахту M - перевести N аккаунт в M шахту (M = ID).
		N шахта - информация о текущей шахте для N аккаунта.
		N работать T - указать текст капчи T и начать работать на аккаунте N.
		N поиск - начать поиск шахт на N аккаунте.
		Добавить аккаунт N M - добавить аккаунт с N логином и M паролем.
		Установить чат N - установить чат для уведомлений N.
		Hlp - вывести эту справку.

		Автоматическая проверка шахты и аккаунта каждые 5 минут.
		'''
#		self.auth()
#		self.auto()
#		exit()
		self.monitor()

	def auth(self, bid):
		pos = {
		'LOGIN_redirect': '1',
		'login'			: codecs.encode(self.acc['users'][bid]['login'], 'cp1251'),
		'lreseted'		: '1',
		'pass'			: codecs.encode(self.acc['users'][bid]['pass'], 'cp1251'),
		'pliv'			: time.localtime()[5]*60,
		'x'				: random.randint(20,99),
		'y'				: random.randint(20,99),
		}
		try: data = requests.post('http://www.heroeswm.ru/login.php', data=pos, headers=self.headers, allow_redirects=False)
		except Exception as e:
			print('Error while authorizing:', e)
			return 0
		data.encoding = 'windows-1251'
		self.acc['users'][bid]['cookies'] = data.cookies
		print(data.cookies)

	def getParamsFromShaht(self, tab):
		i = 0
		tables = []
		tmp = ''
		osn = ''
		while i < len(tab):
			if tab[i][-1] == ':':
				osn += tab[i]
				i += 1
				while i < len(tab):
					if not ':' in tab[i]:
						tmp += tab[i]
						i += 1
					else:
						tables.append(osn + ' ' + tmp)
						tmp = ''
						osn = ''
						break
			else:
				tables.append(tab[i])
				i += 1
		return tables
		
	def auto(self, bid):
		
		arr_can_dig = []
		
		print('Start search..')
		
		data_pr = webrequest('http://www.heroeswm.ru/map.php?st=mn', headers=self.headers, cookies=self.acc['users'][bid]['cookies'], allow_redirects=False)
		data_pr.encoding = 'windows-1251'
		data = webrequest('http://www.heroeswm.ru/map.php?st=sh', headers=self.headers, cookies=self.acc['users'][bid]['cookies'], allow_redirects=False)
		data.encoding = 'windows-1251'
		tmp_pr = re.findall(r'object-info\.php\?id=(\d+)', data_pr.text)
		tmp = re.findall(r'object-info\.php\?id=(\d+)', data.text)
		ids = [e for i,e in enumerate( tmp ) if e not in tmp[:i]] + [e for i,e in enumerate( tmp_pr ) if e not in tmp_pr[:i]]
		for q in ids:
			data = webrequest('http://www.heroeswm.ru/object-info.php?id=' + q, headers=self.headers, cookies=self.acc['users'][bid]['cookies'], allow_redirects=False)
			data.encoding = 'windows-1251'
			if 'Введите код с картинки и нажмите кнопку' in data.text:
				soup = BeautifulSoup(data.text, 'html.parser')
				tab = soup.find('td', {'width': '100%', 'valign': 'top', 'align': 'left'})
				tab = tab.stripped_strings if tab else []
				tab = [x for x in tab]
				tab = self.getParamsFromShaht(tab)
				arr_can_dig.append( 'Шахта #' + q + '\t | \t' + (tab[5]) if (len(tab) > 5) else ('Null' + ' &#128176;'))
				print('Can work in', q, 'shaht')
		return arr_can_dig
					
	def profile(self, bid):
		data = webrequest('http://www.heroeswm.ru/home.php', headers=self.headers, cookies=self.acc['users'][bid]['cookies'], allow_redirects=False)
		data.encoding = 'windows-1251'
		tables = re.findall(r'<td>([,\d]+)</td>', data.text)
		if not tables:
			self.acc['users'][bid]['authorized'] = False
			return False
		else:
			self.acc['users'][bid]['profile_data'] = tables
			return True
	
	def shaht(self, caid, bid):
		data = webrequest('http://www.heroeswm.ru/object-info.php?id=' + caid, headers=self.headers, cookies=self.acc['users'][bid]['cookies'], allow_redirects=False)
		data.encoding = 'windows-1251'
		requests.cookies.merge_cookies(self.acc['users'][bid]['cookies'], data.cookies)
		soup = BeautifulSoup(data.text, 'html.parser')
		tab = soup.find('td', {'width': '100%', 'valign': 'top', 'align': 'left'})
		tab = tab.stripped_strings if tab else []
		tab = [x for x in tab]
		tables = self.getParamsFromShaht(tab)
		tables = '\n&#9643; '.join(tables)
		self.acc['users'][bid]['captcha'] = ''
		if 'Введите код с картинки и нажмите кнопку' in data.text:
			self.acc['users'][bid]['canwork'] = 1 # http://www.heroeswm.ru/work_codes/16987-110/5522338--407692.jpeg
			self.acc['users'][bid]['captcha'] = 'http://www.heroeswm.ru/' + re.findall(r'(work_codes\/(\d+)\-(\d+)\/(\d+)\-\-(\d+)\.jpeg)', data.text)[0][0]
		elif 'Вы уже устроены' in data.text:
			self.acc['users'][bid]['canwork'] = 2
		elif 'Вы находитесь в другом секторе' in data.text:
			self.acc['users'][bid]['canwork'] = 3
		elif 'Прошло меньше часа' in data.text:
			self.acc['users'][bid]['canwork'] = 4
		elif 'Нет рабочих мест' in data.text:
			self.acc['users'][bid]['canwork'] = 5
		elif 'На объекте недостаточно золота' in data.text:
			self.acc['users'][bid]['canwork'] = 6
		else:
			self.acc['users'][bid]['canwork'] = 0
		if not tables:
			self.acc['users'][bid]['authorized'] = False
			return False
		else:
			self.acc['users'][bid]['carierid'] = caid
			self.acc['users'][bid]['carierdata'] = tables
			return True

	def work(self, cap, bid):
		payload = 'http://www.heroeswm.ru/object_do.php?id='+self.acc['users'][bid]['carierid']+'&code='+cap+'&code_id='+self.acc['users'][bid]['cookies']['l_obj_c']+'&pl_id='+self.acc['users'][bid]['cookies']['pl_id']+'&rand1=0.'+str(random.randint(111111111111111, 999999999999999))+'&rand2=0.'+str(random.randint(111111111111111, 999999999999999))
		data = webrequest(payload, headers=self.headers, cookies=self.acc['users'][bid]['cookies'], allow_redirects=False)
		data.encoding = 'windows-1251'
		if 'Вы устроены на работу' in data.text:
			self.acc['users'][bid]['captcha'] = ''
			self.acc['users'][bid]['canwork'] = 2
			return True
		elif 'Введен неправильный код' in data.text:
			return False
		else:
			return False

	def monitor(self):
		iteration = 0
		while 1:
			sys.stderr.flush()
			sys.stdout.flush()
			data = request('messages.get', {'out': 0, 'count': 1})
			if not 'response' in data:
				print('Error loading messages..')
				continue
			for q in data['response']['items']:
				uid = q['user_id']
				r = q['read_state']
				cid = q['chat_id'] if 'chat_id' in q else 0
				body = q['body']
				mid = q['id']
				if not r:
					print(uid, cid, body, r)
					if re.match(r'(\d) статус', body, re.I):
						bid = int(re.findall(r'(\d) статус', body, re.I)[0])
						if (bid < 1) or (bid > (len(self.acc['users']) - 1)):
							sendmsg(uid, cid, '&#9940; ID должен быть в пределах от 1 до ' + str(len(self.acc['users']) - 1))
							continue
						self.profile( bid )
						sendmsg(uid, cid, 'Аккаунт: ' + self.acc['users'][bid]['login'] + '\nАвторизирован: ' +  ( ('да\nСессия #' + str(self.acc['users'][bid]['cookies']['duration']) + '\nСидим в шахте: ' + (self.acc['users'][bid]['carierid'] if self.acc['users'][bid]['carierid'] else 'не назначена') + '\nРаботаем: ' + ('да' if ((self.acc['users'][bid]['canwork'] == 2) or (self.acc['users'][bid]['canwork'] == 4)) else 'нет')) if self.acc['users'][bid]['authorized'] else 'нет') )
					elif re.match(r'Статус', body, re.I):
						accs = [ str(i) + '. ' + str(x['login']) for i, x in enumerate(self.acc['users']) if i > 0]
						sendmsg(uid, cid, 'Статус бота:\nВремя работы: ' + gettime(int(time.time()) - self.time) + '\nАккаунтов: ' + str(len(self.acc['users']) - 1) + '\n' + '\n'.join(accs))
					elif re.match(r'Установить чат', body, re.I):
						if cid > 0:
							self.acc['bot']['chat'] = cid
							sendmsg(uid, cid, 'Чат для уведомлений установлен: '+str(cid))
						else:
							sendmsg(uid, cid, 'Можно установить только групповой чат.')
					elif re.match(r'(справка|помощь|пмщ|hlp|команды)', body, re.I):
						sendmsg(uid, cid, self.help)
					elif re.match(r'(\d) (Войти|Вход)', body, re.I):
						bid = int(re.findall(r'(\d) (Войти|Вход)', body, re.I)[0][0])
						if (bid < 1) or (bid > (len(self.acc['users']) - 1)):
							sendmsg(uid, cid, '&#9940; ID должен быть в пределах от 1 до ' + str(len(self.acc['users']) - 1))
							continue
						if not self.acc['users'][bid]['authorized']:
							self.auth(bid)
							if 'duration' in self.acc['users'][bid]['cookies']:
								self.acc['users'][bid]['authorized'] = True
								sendmsg(uid, cid, '&#9989; Успешно.\nНомер сессии: ' + self.acc['users'][bid]['cookies']['duration'])
							else:
								sendmsg(uid, cid, '&#9940; Не удалось авторизироваться.')
						else:
							sendmsg(uid, cid, '&#9940; Уже авторизован.')
					elif re.match(r'(\d) (Профиль|Баланс)', body, re.I):
						bid = int(re.findall(r'(\d) (Профиль|Баланс)', body, re.I)[0][0])
						if (bid < 1) or (bid > (len(self.acc['users']) - 1)):
							sendmsg(uid, cid, '&#9940; ID должен быть в пределах от 1 до ' + str(len(self.acc['users']) - 1))
							continue
						if self.acc['users'][bid]['authorized']:
							rt = self.profile(bid)
							if rt:
								payl = ''
								if not (self.acc['users'][bid]['profile_data'][0] == '0'): payl += '\nЗолото: ' 	+ str(self.acc['users'][bid]['profile_data'][0])
								if not (self.acc['users'][bid]['profile_data'][1] == '0'): payl += '\nДерево: ' 	+ str(self.acc['users'][bid]['profile_data'][1])
								if not (self.acc['users'][bid]['profile_data'][2] == '0'): payl += '\nРуда: ' 		+ str(self.acc['users'][bid]['profile_data'][2])
								if not (self.acc['users'][bid]['profile_data'][3] == '0'): payl += '\nРтуть: ' 		+ str(self.acc['users'][bid]['profile_data'][3])
								if not (self.acc['users'][bid]['profile_data'][4] == '0'): payl += '\nСеребро: ' 	+ str(self.acc['users'][bid]['profile_data'][4])
								if not (self.acc['users'][bid]['profile_data'][5] == '0'): payl += '\nКристаллы: ' 	+ str(self.acc['users'][bid]['profile_data'][5])
								if not (self.acc['users'][bid]['profile_data'][6] == '0'): payl += '\nСамоцветы: ' 	+ str(self.acc['users'][bid]['profile_data'][6])
								if not (self.acc['users'][bid]['profile_data'][7] == '0'): payl += '\nБриллианты: ' + str(self.acc['users'][bid]['profile_data'][7])
								sendmsg(uid, cid, '&#128176; Ресурсы:' + payl)
							else:
								sendmsg(uid, cid, '&#9940; Не удалось получить данные.\nВозможно, требуется заново авторизироваться.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					elif re.match(r'(\d) (В шахту (\d+)|Шахта)', body, re.I):
						bid = int(re.findall(r'(\d) (В шахту (\d+)|Шахта)', body, re.I)[0][0])
						if (bid < 1) or (bid > (len(self.acc['users']) - 1)):
							sendmsg(uid, cid, '&#9940; ID должен быть в пределах от 1 до ' + str(len(self.acc['users']) - 1))
							continue
						no = re.findall(r'шахту (\d+)', body, re.I)
						if self.acc['users'][bid]['authorized']:
							if (not self.acc['users'][bid]['carierid']) and (not no):
								sendmsg(uid, cid, '&#9940; Шахта не выбрана.')
							else:
								ch = self.shaht(no[0] if no else self.acc['users'][bid]['carierid'], bid)
								if ch:
									if self.acc['users'][bid]['canwork'] == 1:
										wrk = '&#9989; Здесь можно работать.'
									elif self.acc['users'][bid]['canwork'] == 2:
										wrk = '&#9940; Вы уже работаете здесь.'
									elif self.acc['users'][bid]['canwork'] == 3:
										wrk = '&#9940; Вы в другом секторе.'
									elif self.acc['users'][bid]['canwork'] == 4:
										wrk = '&#9940; Прошло меньше часа.'
									elif self.acc['users'][bid]['canwork'] == 5:
										wrk = '&#9940; Нет мест.'
									elif self.acc['users'][bid]['canwork'] == 6:
										wrk = '&#9940; В шахте нет золота.'
									else:
										wrk = 'Здесь нельзя работать. (неизвестная ошибка)'
									cardata = '&#9643; ' + self.acc['users'][bid]['carierdata']
									sendmsg(uid, cid, 'В шахте #' + self.acc['users'][bid]['carierid'] + '\n' + cardata + '\n' + wrk, attach = load(self.acc['users'][bid]['captcha']) if self.acc['users'][bid]['captcha'] else '')
								else:
									sendmsg(uid, cid, '&#9940; Не удалось перейти в шахту.\nШахта не существует / не удалось получить данные / слетела авторизация.\nТекущее значение ID шахты ('+str(self.acc['users'][bid]['carierid'])+') не изменилось.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					elif re.match(r'(\d) работать (.+)', body, re.I):
						bid = int(re.findall(r'(\d) Работать (.+)', body, re.I)[0][0])
						if (bid < 1) or (bid > (len(self.acc['users']) - 1)):
							sendmsg(uid, cid, '&#9940; ID должен быть в пределах от 1 до ' + str(len(self.acc['users']) - 1))
							continue
						text = re.findall(r'работать (.+)', body, re.I)[0]
						if self.acc['users'][bid]['authorized']:
							if self.acc['users'][bid]['carierid']:
								self.shaht(self.acc['users'][bid]['carierid'], bid)
								if self.acc['users'][bid]['canwork'] == 1:
									ch = self.work(text, bid)
									if ch:
										sendmsg(uid, cid, '&#9989; Вы успешно устроились на работу.\nСпасибо, что ввели капчу &#128522;')
									else:
										sendmsg(uid, cid, '&#9940; Неверно введена капча или другая ошибка.\nОбновите состяние шахты командой "'+str(bid)+' шахта".')
								else:
									sendmsg(uid, cid, '&#9940; Вы не можете сейчас работать.')
							else:
								sendmsg(uid, cid, '&#9940; Не выбрана шахта.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					elif re.match(r'(\d) поиск', body, re.I):
						bid = int(re.findall(r'(\d) поиск', body, re.I)[0])
						if (bid < 1) or (bid > (len(self.acc['users']) - 1)):
							sendmsg(uid, cid, '&#9940; ID должен быть в пределах от 1 до ' + str(len(self.acc['users']) - 1))
							continue
						if self.acc['users'][bid]['authorized']:
							if self.acc['users'][bid]['canwork'] != 2:
								tmp = '&#128347;,&#128359;,&#128336;,&#128348;,&#128337;,&#128349;,&#128338;,&#128350;,&#128339;,&#128351;,&#128340;,&#128352;,&#128341;,&#128342;,&#128343;,&#128344;,&#128345;,&#128346;,&#128353;,&#128354;,&#128355;,&#128356;,&#128357;,&#128358;'.split(',')
								emoj = random.choice(tmp)
								sendmsg(uid, cid, emoj + ' Поиск займет некоторое время.')
								arr_s = self.auto(bid)
								if len(arr_s) > 0:
									sendmsg(uid, cid, '&#9989; Список доступных шахт:\n\n&#9643; ' + '\n&#9643; '.join(arr_s))
								else:
									sendmsg(uid, cid, '&#9940; Не было найдено подходящих шахт.')
							else:
								sendmsg(uid, cid, '&#9940; Сейчас нельзя искать шахты.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					elif re.match(r'Добавить аккаунт (.+) (.+)', body, re.I):
						arr = re.findall(r'аккаунт (.+) (.+)', body, re.I)[0]
						log, pas = arr
						updateacc(arr,)
						self.acc['users'].append( { 'login': log, 'pass': pas, 'carierid': 0, 'canwork': 0, 'carierdata': '', 'captcha': '', 'cookies': [], 'authorized': False, 'profile_data': '' } )
						sendmsg(uid, cid, '&#9989; Аккаунт добавлен.')
					else:
						data = request('messages.markAsRead', {'message_ids': mid})
			time.sleep(5)
			for bid in range(1, len(self.acc['users'])):
				if not self.acc['users'][bid]['canwork'] == 1:
					iteration += 1
					if (iteration % 60) == 0 and self.acc['users'][bid]['authorized'] and self.acc['users'][bid]['carierid']:
						ch = self.shaht(self.acc['users'][bid]['carierid'], bid)
						if self.acc['users'][bid]['authorized']:
							if self.acc['users'][bid]['canwork'] == 1:
								sendmsg(0, self.acc['bot']['chat'], '(' + str(bid) + ') ' + self.acc['users'][bid]['login'] + ' сообщает:\n&#9989; В шахте ' + self.acc['users'][bid]['carierid'] + ' можно работать.', attach=load(self.acc['users'][bid]['captcha']))
						else:
							sendmsg(0, self.acc['bot']['chat'], '(' + str(bid) + ') ' + self.acc['users'][bid]['login'] + ' сообщает:\n&#9940; Слетела авторизация. Нужно заново войти в игру.')

def gettime(t):
	temp = time.strftime("%d:%H:%M:%S", time.gmtime(t + 1)).split(':')
	day = int(temp[0]) - 1
	hour = int(temp[1])
	minn = int(temp[2])
	sec = int(temp[3])
	mapp = [day, hour, minn, sec]
	if day > 0:
		return str(mapp[0]) + ' д. ' + str(mapp[1]) + ' ч. ' + str(mapp[2]) + ' м. ' + str(mapp[3]) + ' с.'
	if hour > 0:
		return str(mapp[1]) + ' ч. ' + str(mapp[2]) + ' м. ' + str(mapp[3]) + ' с.'
	if minn > 0:
		return str(mapp[2]) + ' м. ' + str(mapp[3]) + ' с.'
	if sec > 0:
		return str(mapp[3]) + ' с.'

def sendmsg(uid, cid, message, attach=''):
	while True:
		if cid > 0:
			print('[MESSAGES] SEND ' + '0' + ' -> C: ' + str(cid))
			re = request('messages.send', {'chat_id': cid, 'message': message, 'attachment': attach})
		else:
			print('[MESSAGES] SEND ' + '0' + ' -> U: ' + str(uid))
			re = request('messages.send', {'user_id': uid, 'message': message, 'attachment': attach})
		try:
			error = re['error']['error_code']
			print('[MESSAGES] Error code: ' + str(error))
		except:
			break
	return 0

def webrequest(url, headers=[], cookies=None, allow_redirects=True):
	while True:
		try: br = requests.get(url, headers=headers, cookies=cookies, allow_redirects=allow_redirects)
		except Exception as e:
			print('Error while requesting:', e)
			continue
		if br.ok:
			break
	return br

def request(method, params):
	global DATA
	url = 'https://api.vk.com/method/' + method
	params.update({'access_token': DATA['bot']['token'], 'v': '5.52'})
	print('[REQUEST] Make request..')
	while True:
		try:
			br = requests.post(url, data=params, timeout=15)
			if br.ok:
				data = br.json()
				if 'error' in data:
					if data['error']['error_code'] == 6:
						time.sleep(2)
						continue
					else:
						print('[REQUEST] Error:', data)
						break
				else:
					print('[REQUEST] OK')
					break
		except Exception as e:
			print('[REQUEST] Exception:', e)
			time.sleep(1)
	return data

def load_image(path):
	resp = request('photos.getMessagesUploadServer', {})
	try:
		if 'response' in resp:
			url = resp['response']['upload_url']
		else:
			return ''
	except:
		return ''
	files = {'photo': open(path, 'rb')}
	try:
		r = requests.post(url, files=files)
		if r.ok:
			server = r.json()['server']
			photo = r.json()['photo']
			hashh = r.json()['hash']
		else:
			return ''
	except:
		return ''
	try:
		save = request('photos.saveMessagesPhoto', {'photo': photo, 'server': server, 'hash': hashh})['response'][0]['id']
	except:
		save = ''
	return 'photo' + DATA['bot']['botid'] + '_' + str(save)

def load(url):
	pat = sys.path[0] + '/captcha.jpg'
	try:
		p = requests.get(url)
	except Exception as e:
		print('ImSer exception:', e)
		return ''
	out = open(pat, 'wb')
	out.write(p.content)
	out.close()
	return load_image(pat)

def updateacc(data):
	global DATA
	config = configparser.ConfigParser()
	config['BOT'] = {	'token'	: DATA['bot']['token'],
						'botid'	: DATA['bot']['botid'],
						'chat'	: DATA['bot']['chat'],	}
	for i,q in enumerate(DATA['users'][1:]):
		config['USER'+str(i)] = {	'login'	: q['login'],
									'pass'	: q['pass'],	}
	config['USER'+str(len( DATA['users'] ) - 1)] = {'login': data[0], 'pass': data[1], }
	with open(sys.path[0] + '/acc.ini', 'w') as configfile:
		config.write(configfile)
	return 0

def loadacc():
	global DATA
	config = configparser.ConfigParser()
	config.read(sys.path[0] + '/acc.ini')
	accs = config.sections()
	for q in accs:
		if q == 'BOT':
			DATA['bot'] = {'token': config[q]['token'], 'botid': config[q]['botid'], 'chat': int(config[q]['chat']) }
		if 'USER' in q:
			DATA['users'].append( { 'login': config[q]['login'], 'pass': config[q]['pass'], 'carierid': 0, 'canwork': 0, 'carierdata': '', 'captcha': '', 'cookies': [], 'authorized': False, 'profile_data': '' } )

def setup_console(sys_enc="utf-8"):
	import codecs
	try:
		if sys.platform.startswith("win"):
			import ctypes
			enc = "cp%d" % ctypes.windll.kernel32.GetOEMCP()
		else:
			enc = (sys.stdout.encoding if sys.stdout.isatty() else
						sys.stderr.encoding if sys.stderr.isatty() else
							sys.getfilesystemencoding() or sys_enc)
		sys.setdefaultencoding(sys_enc)
		if sys.stdout.isatty() and sys.stdout.encoding != enc:
			sys.stdout = codecs.getwriter(enc)(sys.stdout, 'replace')
		if sys.stderr.isatty() and sys.stderr.encoding != enc:
			sys.stderr = codecs.getwriter(enc)(sys.stderr, 'replace')
	except:
		pass
	
if __name__ == '__main__':
	setup_console()
	try:
		flag = int(sys.argv[1])
	except:
		print('1 or 0 expected..')
		exit()
	if flag == 0:
		sys.stderr = open(sys.path[0] + '/err.txt', 'w')
		sys.stdout = open(sys.path[0] + '/log.txt', 'w')
	bot()
	exit()
