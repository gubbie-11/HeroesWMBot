import requests
import time
import random
import sys
import re
import configparser
from bs4 import BeautifulSoup

DATA = []

class bot():

	def __init__(self):
		loadacc()
		self.time = int(time.time())
		self.carierid = '0'
		self.canwork = 0
		self.carierdata = []
		self.captcha = ''
		self.acc = DATA
		self.chat = int(self.acc[4])
		self.headers = {   'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0',
					       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					       'Connection': 'keep-alive',
					       'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'}
		self.cookies = []
		self.authorized = False
		self.help = '''Справка по командам:

		Статус - статус бота.
		Вход/Войти - войти в аккаунт.
		Профиль - информация о профиле
		В шахту N - перейти в N шахту (N = ID).
		Шахта - информация о текущей шахте.
		Работать T - указать текст капчи T и начать работать.
		Hlp - вывести эту справку.

		Автоматическая проверка шахты и аккаунта каждые 5 минут.
		'''
#		self.auth()
#		self.auto()
#		exit()
		self.monitor()

	def auth(self):
		log, pas = self.acc[:2]
		pos = {
		'LOGIN_redirect': '1',
		'login': log,
		'lreseted': '1',
		'pass': pas,
		'pliv': time.localtime()[5]*60,
		'x': random.randint(20,99),
		'y': random.randint(20,99),
		}
		data = requests.post('http://www.heroeswm.ru/login.php', data=pos, headers=self.headers, allow_redirects=False)
		self.cookies = data.cookies
		print(self.cookies)

	def getParamsFromShaht(self, tab):
		i = 0
		tables = []
		tmp = ''
		osn = ''
		# Просто парсер. Иди дальше
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
		
	def auto(self):
		
		arr_can_dig = []
		
		print('Start search..')
		
		data_pr = requests.get('http://www.heroeswm.ru/map.php?st=mn', headers=self.headers, cookies=self.cookies, allow_redirects=False)
		data_pr.encoding = 'windows-1251'
		data = requests.get('http://www.heroeswm.ru/map.php?st=sh', headers=self.headers, cookies=self.cookies, allow_redirects=False)
		data.encoding = 'windows-1251'
		tmp_pr = re.findall(r'object-info\.php\?id=(\d+)', data_pr.text)
		tmp = re.findall(r'object-info\.php\?id=(\d+)', data.text)
		ids = [e for i,e in enumerate( tmp ) if e not in tmp[:i]] + [e for i,e in enumerate( tmp_pr ) if e not in tmp_pr[:i]]
		for q in ids:
			data = requests.get('http://www.heroeswm.ru/object-info.php?id=' + q, headers=self.headers, cookies=self.cookies, allow_redirects=False)
			data.encoding = 'windows-1251'
			if 'Введите код с картинки и нажмите кнопку' in data.text:
				soup = BeautifulSoup(data.text, 'html.parser')
				tab = soup.find('td', {'width': '100%', 'valign': 'top', 'align': 'left'})
				tab = tab.stripped_strings if tab else []
				tab = [x for x in tab]
				tab = self.getParamsFromShaht(tab)
				arr_can_dig.append( 'Шахта #' + q + '\t | \t' + tab[5] + ' &#128176;')
				print('Can work in', q, 'shaht')
		return arr_can_dig
			
		
	def profile(self):
		data = requests.get('http://www.heroeswm.ru/home.php', headers=self.headers, cookies=self.cookies, allow_redirects=False)
		data.encoding = 'windows-1251'
		tables = re.findall(r'<td>([,\d]+)</td>', data.text)
		if not tables:
			self.authorized = False
			return False
		else:
			self.profile_data = tables
			return True

	
	def shaht(self, caid):
		data = requests.get('http://www.heroeswm.ru/object-info.php?id=' + caid, headers=self.headers, cookies=self.cookies, allow_redirects=False)
		data.encoding = 'windows-1251'
		requests.cookies.merge_cookies(self.cookies, data.cookies)
		soup = BeautifulSoup(data.text, 'html.parser')
		tab = soup.find('td', {'width': '100%', 'valign': 'top', 'align': 'left'})
		tab = tab.stripped_strings if tab else []
		tab = [x for x in tab]
		tables = self.getParamsFromShaht(tab)
		tables = '\n&#9643; '.join(tables)
		self.captcha = ''
		if 'Введите код с картинки и нажмите кнопку' in data.text:
			self.canwork = 1 # http://www.heroeswm.ru/work_codes/16987-110/5522338--407692.jpeg
			self.captcha = 'http://www.heroeswm.ru/' + re.findall(r'(work_codes\/(\d+)\-(\d+)\/(\d+)\-\-(\d+)\.jpeg)', data.text)[0][0]
		elif 'Вы уже устроены' in data.text:
			self.canwork = 2
		elif 'Вы находитесь в другом секторе' in data.text:
			self.canwork = 3
		elif 'Прошло меньше часа' in data.text:
			self.canwork = 4
		elif 'Нет рабочих мест' in data.text:
			self.canwork = 5
		elif 'На объекте недостаточно золота' in data.text:
			self.canwork = 6
		else:
			self.canwork = 0
		if not tables:
			self.authorized = False
			return False
		else:
			self.carierid = caid
			self.carierdata = tables
			return True

	def work(self, cap):
		payload = 'http://www.heroeswm.ru/object_do.php?id='+self.carierid+'&code='+cap+'&code_id='+self.cookies['l_obj_c']+'&pl_id='+self.cookies['pl_id']+'&rand1=0.'+str(random.randint(111111111111111, 999999999999999))+'&rand2=0.'+str(random.randint(111111111111111, 999999999999999))
		data = requests.get(payload, headers=self.headers, cookies=self.cookies, allow_redirects=False)
		data.encoding = 'windows-1251'
		if 'Вы устроены на работу' in data.text:
			self.captcha = ''
			self.canwork = 2
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
					if re.match(r'Статус', body, re.I):
						self.profile()
						sendmsg(uid, cid, 'Статус бота:\nВремя работы: ' + gettime(int(time.time()) - self.time) + '\nТекущий аккаунт: ' + self.acc[0] + '\nАвторизирован: ' +  ( ('да\nСессия #' + str(self.cookies['duration']) + '\nСидим в шахте: ' + (self.carierid if self.carierid else 'не назначена') + '\nРаботаем: ' + ('да' if ((self.canwork == 2) or (self.canwork == 4)) else 'нет')) if self.authorized else 'нет') )
					elif re.match(r'(справка|помощь|пмщ|hlp|команды)', body, re.I):
						sendmsg(uid, cid, self.help)
					elif re.match(r'(Войти|Вход)', body, re.I):
						if not self.authorized:
							self.auth()
							if 'duration' in self.cookies:
								self.authorized = True
								sendmsg(uid, cid, '&#9989; Успешно.\nНомер сессии: ' + self.cookies['duration'])
							else:
								sendmsg(uid, cid, '&#9940; Не удалось авторизироваться.')
						else:
							sendmsg(uid, cid, '&#9940; Уже авторизован.')
					elif re.match(r'(Профиль|Баланс)', body, re.I):
						if self.authorized:
							rt = self.profile()
							if rt:
								payl = ''
								if not (self.profile_data[0] == '0'): payl += '\nЗолото: ' + str(self.profile_data[0])
								if not (self.profile_data[1] == '0'): payl += '\nДерево: ' + str(self.profile_data[1])
								if not (self.profile_data[2] == '0'): payl += '\nРуда: ' + str(self.profile_data[2])
								if not (self.profile_data[3] == '0'): payl += '\nРтуть: ' + str(self.profile_data[3])
								if not (self.profile_data[4] == '0'): payl += '\nСеребро: ' + str(self.profile_data[4])
								if not (self.profile_data[5] == '0'): payl += '\nКристаллы: ' + str(self.profile_data[5])
								if not (self.profile_data[6] == '0'): payl += '\nСамоцветы: ' + str(self.profile_data[6])
								if not (self.profile_data[7] == '0'): payl += '\nБриллианты: ' + str(self.profile_data[7])
								sendmsg(uid, cid, '&#128176; Ресурсы:' + payl)
							else:
								sendmsg(uid, cid, '&#9940; Не удалось получить данные.\nВозможно, требуется заново авторизироваться.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					elif re.match(r'(В шахту (\d+)|Шахта)', body, re.I):
						no = re.findall(r'шахту (\d+)', body, re.I)
						if self.authorized:
							if (not self.carierid) and (not no):
								sendmsg(uid, cid, '&#9940; Шахта не выбрана.')
							else:
								ch = self.shaht(no[0] if no else self.carierid)
								if ch:
									if self.canwork == 1:
										wrk = '&#9989; Здесь можно работать.'
									elif self.canwork == 2:
										wrk = '&#9940; Вы уже работаете здесь.'
									elif self.canwork == 3:
										wrk = '&#9940; Вы в другом секторе.'
									elif self.canwork == 4:
										wrk = '&#9940; Прошло меньше часа.'
									elif self.canwork == 5:
										wrk = '&#9940; Нет мест.'
									elif self.canwork == 6:
										wrk = '&#9940; В шахте нет золота.'
									else:
										wrk = 'Здесь нельзя работать. (неизвестная ошибка)'
									cardata = '&#9643; ' + self.carierdata
									sendmsg(uid, cid, 'В шахте #' + self.carierid + '\n' + cardata + '\n' + wrk, attach = load(self.captcha) if self.captcha else '')
								else:
									sendmsg(uid, cid, '&#9940; Не удалось перейти в шахту.\nШахта не существует / не удалось получить данные / слетела авторизация.\nТекущее значение ID шахты ('+self.carierid+') не изменилось.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					elif re.match(r'Работать (.+)', body, re.I):
						text = re.findall(r'работать (.+)', body, re.I)[0]
						if self.authorized:
							if self.carierid:
								self.shaht(self.carierid)
								if self.canwork == 1:
									ch = self.work(text)
									if ch:
										sendmsg(uid, cid, '&#9989; Вы успешно устроились на работу. Спасибо, что ввели капчу &#128522;')
									else:
										sendmsg(uid, cid, '&#9940; Неверно введена капча или другая ошибка.\nОбновите состяние шахты командой "Шахта".')
								else:
									sendmsg(uid, cid, '&#9940; Вы не можете сейчас работать.')
							else:
								sendmsg(uid, cid, '&#9940; Не выбрана шахта.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					elif re.match(r'Поиск', body, re.I):
						if self.authorized:
							if self.canwork != 2:
								tmp = '&#128347;,&#128359;,&#128336;,&#128348;,&#128337;,&#128349;,&#128338;,&#128350;,&#128339;,&#128351;,&#128340;,&#128352;,&#128341;,&#128342;,&#128343;,&#128344;,&#128345;,&#128346;,&#128353;,&#128354;,&#128355;,&#128356;,&#128357;,&#128358;'.split(',')
								emoj = random.choice(tmp)
								sendmsg(uid, cid, emoj + ' Поиск займет некоторое время.')
								arr_s = self.auto()
								if len(arr_s) > 0:
									sendmsg(uid, cid, '&#9989; Список доступных шахт:\n\n&#9643; ' + '\n&#9643; '.join(arr_s))
								else:
									sendmsg(uid, cid, '&#9940; Не было найдено подходящих шахт.')
							else:
								sendmsg(uid, cid, '&#9940; Сейчас нельзя искать шахты.')
						else:
							sendmsg(uid, cid, '&#9940; Не авторизован.')
					else:
						data = request('messages.markAsRead', {'message_ids': mid})
			time.sleep(5)
			if not self.canwork == 1:
				iteration += 1
				if (iteration % 60) == 0 and self.authorized and self.carierid:
					ch = self.shaht(self.carierid)
					if self.authorized:
						if self.canwork == 1:
							sendmsg(0, self.chat, '&#9989; В шахте ' + self.carierid + ' можно работать.', attach=load(self.captcha))
					else:
						sendmsg(0, self.chat, '&#9940; Слетела авторизация. Нужно заново войти в игру.')

def gettime(t):
	temp = time.strftime("%d:%H:%M:%S", time.gmtime(t + 1)).split(':')
	day = int(temp[0]) - 1
	hour = int(temp[1])
	min = int(temp[2])
	sec = int(temp[3])
	map = [day, hour, min, sec]
	if day > 0:
		return str(map[0]) + ' д. ' + str(map[1]) + ' ч. ' + str(map[2]) + ' м. ' + str(map[3]) + ' с.'
	if hour > 0:
		return str(map[1]) + ' ч. ' + str(map[2]) + ' м. ' + str(map[3]) + ' с.'
	if min > 0:
		return str(map[2]) + ' м. ' + str(map[3]) + ' с.'
	if sec > 0:
		return str(map[3]) + ' с.'

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

def request(method, params):
	global DATA
	url = 'https://api.vk.com/method/' + method
	params.update({'access_token': DATA[2], 'v': '5.52'})
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
			hash = r.json()['hash']
		else:
			return ''
	except:
		return ''
	try:
		save = request('photos.saveMessagesPhoto', {'photo': photo, 'server': server, 'hash': hash})['response'][0]['id']
	except:
		save = ''
	return 'photo' + DATA[3] + '_' + str(save)

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

def loadacc():
	global DATA
	config = configparser.ConfigParser()
	config.read(sys.path[0] + '/acc.ini')
	DATA = [config['USER']['login'], config['USER']['pass'], config['USER']['token'], config['USER']['botid'], config['USER']['chat']]

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
