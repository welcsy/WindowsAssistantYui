import sys
import os
import pyttsx3
import json
from openai import OpenAI
import config
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMenu, QAction, QTextEdit, QVBoxLayout, QLineEdit
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QPoint, QTimer

def resource_path(relative_path):
	"""Get absolute path to resource, works for dev and PyInstaller"""
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except AttributeError:
		# Running as script
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)

def get_conversation_file():
	"""Get writable conversation file path, copy from resources if needed"""
	# 使用用戶家目錄下的 .myAI 資料夾
	app_dir = os.path.join(os.path.expanduser("~"), ".myAI")
	conversation_file = os.path.join(app_dir, "conversation.txt")
	print(app_dir)
	print(conversation_file)
	
	# 確保資料夾存在
	if not os.path.exists(app_dir):
		try:
			os.makedirs(app_dir)
			print(f"Created directory {app_dir}")
		except Exception as e:
			print(f"Error creating directory {app_dir}: {e}")
			return conversation_file
	
	# 若 conversation.txt 不存在，嘗試從資源複製
	if not os.path.exists(conversation_file):
		source_file = resource_path("conversation.txt")
		print(f"Checking conversation.txt at {source_file}")
		if os.path.exists(source_file):
			try:
				# 讀取資源並寫入目標
				with open(source_file, 'r', encoding='utf-8') as src:
					content = src.read()
				with open(conversation_file, 'w', encoding='utf-8') as dst:
					dst.write(content)
				print(f"Copied conversation.txt to {conversation_file}")
			except Exception as e:
				print(f"Error copying conversation.txt: {e}")
				# 創建空白檔案
				try:
					with open(conversation_file, 'w', encoding='utf-8') as f:
						f.write("")
					print(f"Created empty conversation.txt at {conversation_file}")
				except Exception as e:
					print(f"Error creating conversation.txt: {e}")
		else:
			try:
				with open(conversation_file, 'w', encoding='utf-8') as f:
					f.write("")
				print(f"Created empty conversation.txt at {conversation_file}")
			except Exception as e:
				print(f"Error creating conversation.txt: {e}")
	
	return conversation_file

def get_emotion_file():
	"""Get emotion.txt file path, copy from resources if needed"""
	# 使用用戶家目錄下的 .myAI 資料夾
	app_dir = os.path.join(os.path.expanduser("~"), ".myAI")
	emotion_file = os.path.join(app_dir, "emotion.txt")
	
	# 確保資料夾存在
	if not os.path.exists(app_dir):
		try:
			os.makedirs(app_dir)
			print(f"Created directory {app_dir}")
		except Exception as e:
			print(f"Error creating directory {app_dir}: {e}")
			return emotion_file
	
	# 若 emotion.txt 不存在，嘗試從資源複製
	if not os.path.exists(emotion_file):
		source_file = resource_path("emotion.txt")
		print(f"Checking emotion.txt at {source_file}")
		if os.path.exists(source_file):
			try:
				# 讀取資源並寫入目標
				with open(source_file, 'r', encoding='utf-8') as src:
					content = src.read()
				with open(emotion_file, 'w', encoding='utf-8') as dst:
					dst.write(content)
				print(f"Copied emotion.txt to {emotion_file}")
			except Exception as e:
				print(f"Error copying emotion.txt: {e}")
				# 創建預設 emotion.txt
				try:
					with open(emotion_file, 'w', encoding='utf-8') as f:
						f.write("emotion,image_file,description\n")
						f.write("happy,Yui_happy.png,積極、快樂（如「嘿！超開心！」）\n")
					print(f"Created default emotion.txt at {emotion_file}")
				except Exception as e:
					print(f"Error creating emotion.txt: {e}")
		else:
			print(f"Source emotion.txt not found at {source_file}")
		
			# 若資源中無檔案，創建預設 emotion.txt
			try:
				with open(emotion_file, 'w', encoding='utf-8') as f:
					f.write("emotion,image_file,description\n")
					f.write("happy,Yui_happy.png,積極、快樂（如「嘿！超開心！」）\n")
				print(f"Created default emotion.txt at {emotion_file}")
			except Exception as e:
				print(f"Error creating emotion.txt: {e}")
	
	return emotion_file

class ChatWindow(QWidget):
	def __init__(self, conversation_file, openai_client, DesktopAICore):
		super().__init__()
		self.conversation_file = conversation_file
		self.openai_client = openai_client
		self.DesktopAICore = DesktopAICore  # Reference to DesktopAICore for play_sound and update_image
		self.conversation_history = []  # Store conversation history
		self.max_history = 6  # Store up to 3 pairs (user + assistant)
		# 載入情感和範例
		self.emotions, self.emotion_examples = self.load_emotions()
		print(f"Loaded emotions: {self.emotions}")
		print(f"Loaded examples: {self.emotion_examples}")
		self.init_ui()
		# Timer to refresh chat content
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_chat)
		self.timer.start(1000)  # Refresh every 1 second

	def load_emotions(self):
		"""從 emotion.txt 載入情感清單和 Prompt 範例"""
		default_emotions = ["happy"]
		default_examples = {
			"happy": "積極、快樂（如「嘿！超開心！」）"
		}
		# txt_path = resource_path("emotion.txt")
		txt_path = get_emotion_file()
		try:
			with open(txt_path, 'r', encoding='utf-8') as f:
				lines = f.readlines()
			emotions = []
			examples = {}
			for i, line in enumerate(lines):
				line = line.strip()
				if not line or line.startswith('#'):  # 跳過空行或註釋
					continue
				if i == 0 and line == "emotion,image_file,description":  # 跳過標頭
					continue
				# 假設每行格式為：emotion,image_file,description
				parts = line.split(',', 2)  # 分割最多兩次，保留 description 中的逗號
				if len(parts) != 3:
					print(f"Skipping invalid line in emotion.txt: {line}")
					continue
				emotion, _, description = parts
				emotion = emotion.strip().lower()
				description = description.strip()
				if emotion:  # 確保 emotion 不為空
					emotions.append(emotion)
					examples[emotion] = description if description else f"未知情感（如「{emotion} 的語氣」）"
			if not emotions:  # 若無有效情緒
				print("Error: No valid emotions found in emotion.txt")
				return default_emotions, default_examples
			return emotions, examples
		except FileNotFoundError:
			print(f"Error: emotion.txt not found at {txt_path}")
			return default_emotions, default_examples
		except Exception as e:
			print(f"Error loading emotion.txt: {e}")
			return default_emotions, default_examples

	def init_ui(self):
		self.setWindowTitle("聊天室")
		self.setGeometry(300, 300, 400, 300)
		# Layout
		layout = QVBoxLayout()
		# Text area for conversation
		self.chat_display = QTextEdit(self)
		self.chat_display.setReadOnly(True)
		layout.addWidget(self.chat_display)
		# Input area
		self.input_field = QLineEdit(self)
		self.input_field.setPlaceholderText("輸入訊息...")
		self.input_field.returnPressed.connect(self.send_message)
		layout.addWidget(self.input_field)
		self.setLayout(layout)
		# Initial load
		self.update_chat()

	def update_chat(self):
		try:
			if os.path.exists(self.conversation_file):
				with open(self.conversation_file, 'r', encoding='utf-8') as f:
					content = f.read()
				self.chat_display.setPlainText(content)
				# Scroll to bottom
				self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
			else:
				self.chat_display.setPlainText("尚未有對話記錄")
		except Exception as e:
			self.chat_display.setPlainText(f"讀取對話記錄失敗: {e}")

	def send_message(self):
		user_input = self.input_field.text().strip()
		if not user_input:
			return
		# Log user input
		self.log_conversation(user_input=user_input)
		# 第一次呼叫：生成回應
		response = self.get_openai_response(user_input)
		self.log_conversation(ai_response=response)
		# 清空輸入
		self.input_field.clear()		
		# 第二次呼叫：分析回應語氣
		emotion = self.get_emotion_from_response(response)
		print(f"Processing emotion: {emotion}")
		# 直接用 emotion 更新圖片
		self.DesktopAICore.update_image(emotion=emotion)					
		# 播放語音
		self.DesktopAICore.play_sound(response)

	def log_conversation(self, user_input=None, ai_response=None):
		try:
			with open(self.conversation_file, 'a', encoding='utf-8') as f:
				timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				if user_input:
					f.write(f"{timestamp} | User: {user_input}\n")
					print(f"Logged user input: {user_input}")
				if ai_response:
					timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					f.write(f"{timestamp} | AI: {ai_response}\n")
					print(f"Logged AI response: {ai_response}")
		except Exception as e:
			print(f"Error logging conversation: {e}")

	def get_openai_response(self, user_input):
		if not self.openai_client:
			print("OpenAI client not available")
			return "哎呀，出了點問題！"
		self.conversation_history.append({"role": "user", "content": user_input})
		# Trim history to max length
		if len(self.conversation_history) > self.max_history:
			self.conversation_history = self.conversation_history[-self.max_history:]
		try:
			messages=[
				{
					"role": "system",
					"content": (
						"你是一個友好的桌面精靈，名叫 Yui。請用繁體中文回應，語氣熱情且親切，像是和老朋友聊天。"
						"根據用戶輸入生成自然的回應文字，參考之前的對話歷史，保持連貫性。"
						"只返回純文字回應，不要包含 JSON 或其他格式。"
					)
				}
			]
			# Add conversation history
			messages.extend(self.conversation_history)
			response = self.openai_client.chat.completions.create(
				model="gpt-4o-mini",
				messages=messages,
				max_tokens=100,
				temperature=0.7
			)
			response_text = response.choices[0].message.content.strip()
			print(f"OpenAI response: {repr(response_text)}")
			self.conversation_history.append({"role": "assistant", "content": response_text})
			if len(self.conversation_history) > self.max_history:
				self.conversation_history = self.conversation_history[-self.max_history:]
			return response_text
		except Exception as e:
			print(f"OpenAI error: {e}")
			return "哎呀，出了點問題！"

	def get_emotion_from_response(self, response_text):
		if not self.openai_client:
			print("OpenAI client not available")
			return "happy"
		try:
			# 動態生成情感清單和範例
			emotion_list = "」、「".join(self.emotions)
			emotion_options = "|".join(self.emotions)
			examples = "\n".join([f"- {self.emotion_examples[emotion]} → \"{emotion}\"" for emotion in self.emotions])
			messages = [
				{
					"role": "system",
					"content": (
						f"你是一個情感分析助手。請分析以下 Yui 的回應語氣，判斷為「{emotion_list}」，"
						f"以 JSON 格式返回：{{\"emotion\": \"{emotion_options}\"}}。"
						f"情感分析基於回應語氣，例如：\n{examples}\n"
						"請確保回應為有效 JSON 格式，即使無法判斷，也返回：{\"emotion\": \"happy\"}。"
					)
				},
				{
					"role": "user",
					"content": f"分析這段回應的語氣：{response_text}"
				}
			]
			response = self.openai_client.chat.completions.create(
				model="gpt-4o-mini",
				messages=messages,
				max_tokens=50,
				temperature=0.5  # 降低創意，確保 JSON 穩定
			)
			raw_content = response.choices[0].message.content.strip()
			print(f"OpenAI emotion analysis: {repr(raw_content)}")
			try:
				result = json.loads(raw_content)
				if not isinstance(result, dict) or "emotion" not in result:
					print("Invalid JSON structure in emotion analysis")
					return "happy"
				emotion = result["emotion"].strip().lower()
				if emotion not in self.emotions:
					print(f"Emotion {emotion} not found in emotions list")
					return "happy"
				return emotion
			except json.JSONDecodeError as e:
				print(f"JSON decode error in emotion analysis: {e}")
				return "happy"
		except Exception as e:
			print(f"OpenAI error in emotion analysis: {e}")
			return "happy"

	def closeEvent(self, event):
		self.timer.stop()
		event.accept()

class DesktopAICore(QWidget):
	def __init__(self):
		super().__init__()
		# 初始化 OpenAI API
		self.conversation_file = get_conversation_file()		
		self.openai_client = None
		try:
			self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
			print("OpenAI client initialized")
		except Exception as e:
			print(f"OpenAI initialization failed: {e}")
		
		# Chat window
		self.chat_window = None		
		# 載入圖片（動態從 emotion.txt）
		self.images = self.load_images()
		self.current_image = self.images.get("normal", resource_path(os.path.join("pictures", "Yui_normal.png")))
		# 再調用 init_ui 和 init_tts
		self.init_ui()
		self.init_tts()
		# Variables for dragging
		self.dragging = False
		self.drag_position = QPoint()

	def load_images(self):
		"""從 emotion.txt 載入圖片映射，包含 normal 圖片"""
		default_images = {
			"normal": resource_path(os.path.join("pictures", "Yui_normal.png")),
			"happy": resource_path(os.path.join("pictures", "Yui_happy.png"))
		}
		txt_path = get_emotion_file()		
		images = {"normal": default_images["normal"]}
		try:
			with open(txt_path, 'r', encoding='utf-8') as f:
				lines = f.readlines()
			for i, line in enumerate(lines):
				line = line.strip()
				if not line or line.startswith('#'):  # 跳過空行或註釋
					continue
				if i == 0 and line == "emotion,image_file,description":  # 跳過標頭
					continue
				# 假設每行格式為：emotion,image_file,description
				parts = line.split(',', 2)
				if len(parts) != 3:
					print(f"Skipping invalid line in emotion.txt: {line}")
					continue
				emotion, image_file, _ = parts
				emotion = emotion.strip().lower()
				image_file = image_file.strip()
				if emotion and image_file:  # 確保 emotion 和 image_file 不為空
					images[emotion] = resource_path(os.path.join("pictures", image_file))
			if not any(k != "normal" for k in images):
				print("Error: No valid emotions found in emotion.txt")
				return default_images
			print(f"Loaded images: {images}")
			return images
		except FileNotFoundError:
			print(f"Error: emotion.txt not found at {txt_path}")
			return default_images
		except Exception as e:
			print(f"Error loading emotion.txt: {e}")
			return default_images

	def init_ui(self):
		# Main window setup
		self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
		self.setAttribute(Qt.WA_TranslucentBackground)
		self.resize(256, 384)
		self.move(100, 100)

		# Set window icon
		icon_path = resource_path(os.path.join("pictures", "Yui.ico"))  # 可替換為 icon.ico
		if os.path.exists(icon_path):
			self.setWindowIcon(QIcon(resource_path(icon_path)))
			print(f"Icon file {icon_path} found")
		else:
			print(f"Error: Icon file {icon_path} not found")

		# Label to display image
		self.image_label = QLabel(self)
		if os.path.exists(self.current_image):
			self.image_label.setPixmap(QPixmap(self.current_image))
			print(f"Loaded image: {self.current_image}")
		else:
			print(f"Error: Initial image {self.current_image} not found")
		self.image_label.resize(256, 384)

		# Context menu
		self.context_menu = QMenu(self)
		chat_action = QAction("開啟聊天室", self)
		exit_action = QAction("退出", self)

		chat_action.triggered.connect(self.open_chat_window)		
		exit_action.triggered.connect(self.close)

		self.context_menu.addAction(chat_action)		
		self.context_menu.addAction(exit_action)

	def init_tts(self):
		self.tts_engine = pyttsx3.init()
		voices = self.tts_engine.getProperty('voices')
		for voice in voices:
			if 'zh' in voice.id.lower() or 'chinese' in voice.id.lower():
				self.tts_engine.setProperty('voice', voice.id)
				print(f"Set TTS voice to: {voice.id}")
				break
		self.tts_engine.setProperty('rate', 150)  # Speech rate

	def update_image(self, emotion):
		self.current_image = self.images.get(emotion, self.images.get("happy", resource_path(os.path.join("pictures", "Yui_happy.png"))))
		print(f"Updating image to: {self.current_image}")
		if os.path.exists(self.current_image):
			self.image_label.setPixmap(QPixmap(self.current_image))
			app = QApplication.instance()
		else:
			print(f"Error: Image file {self.current_image} not found")
			self.current_image = self.images.get("normal", resource_path(os.path.join("pictures", "Yui_normal.png")))
			if os.path.exists(self.current_image):
				self.image_label.setPixmap(QPixmap(self.current_image))

	def play_sound(self, text):
		try:
			self.tts_engine.say(text)
			self.tts_engine.runAndWait()
		except Exception as e:
			print(f"TTS error: {e}")
			# Fallback to beep if TTS fails
			import winsound
			winsound.Beep(440, 500)

	def open_chat_window(self):
		if self.chat_window is None or not self.chat_window.isVisible():
			self.chat_window = ChatWindow(self.conversation_file, self.openai_client, self)
			self.chat_window.show()
		else:
			self.chat_window.activateWindow()

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.dragging = True
			self.drag_position = event.globalPos() - self.pos()
			event.accept()
		elif event.button() == Qt.RightButton:
			self.context_menu.exec_(event.globalPos())
			event.accept()

	def mouseMoveEvent(self, event):
		if self.dragging and event.buttons() & Qt.LeftButton:
			self.move(event.globalPos() - self.drag_position)
			event.accept()

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.dragging = False
			event.accept()

	def contextMenuEvent(self, event):
		# Override to prevent duplicate right-click handling
		pass

	def closeEvent(self, event):
		if self.chat_window:
			self.chat_window.close()
		event.accept()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	# Set application icon
	icon_path = resource_path(os.path.join("pictures", "Yui.ico"))  # 可替換為 icon.ico
	if os.path.exists(icon_path):
		icon = QIcon(icon_path)
		print(f"icon is null or not? {icon.isNull()}")
		if not icon.isNull():
			app.setWindowIcon(icon)
			print(f"Successfully set application icon: {icon_path}")
		else:
			print(f"Error: Failed to load icon {icon_path}, icon is null")
	else:
		print(f"Error: Icon file {icon_path} not found")
	sprite = DesktopAICore()
	sprite.show()
	sys.exit(app.exec_())
