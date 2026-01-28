#!/usr/bin/env python3
"""
Monkey Gram - Консольное приложение для управления Telegram-аккаунтами
Автор: Monkey Gram Team
Версия: 2.0
"""

import asyncio
import json
import os
import time
import random
import signal
import aiohttp
import socket
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
import getpass

from pyrogram import Client, filters, types, enums
from pyrogram.errors import (
    FloodWait, RPCError, SessionPasswordNeeded,
    PhoneCodeInvalid, PhoneCodeExpired, BadRequest
)


class MonkeyGram:
    """Основной класс приложения Monkey Gram"""
    
    def __init__(self):
        self.config_file = "monkey_config.json"
        self.folders_file = "monkey_folders.json"
        self.auto_reply_file = "monkey_auto_reply.json"
        self.accounts_file = "monkey_accounts.json"
        self.client: Optional[Client] = None
        self.current_account: Optional[Dict] = None
        self.is_running = True
        self.auto_reply_running = False
        self.auto_subscribe_running = False
        self.stop_event = asyncio.Event()
        
    def print_logo(self):
        """Вывод логотипа Monkey Gram"""
        logo = """
        
        \033[1;33m
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  ███╗   ███╗ ██████╗ ███╗   ██╗██╗  ██╗███████╗██╗   ██╗  ║
║  ████╗ ████║██╔═══██╗████╗  ██║██║ ██╔╝██╔════╝╚██╗ ██╔╝  ║
║  ██╔████╔██║██║   ██║██╔██╗ ██║█████╔╝ █████╗   ╚████╔╝   ║
║  ██║╚██╔╝██║██║   ██║██║╚██╗██║██╔═██╗ ██╔══╝    ╚██╔╝    ║
║  ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║  ██╗███████╗   ██║     ║
║  ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝     ║
║                                                            ║
║                    🐒 Telegram Manager v2.0 🐒            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
        \033[0m
        """
        print(logo)
    
    def print_monkey(self):
        """Рисуем обезьянку"""
        monkey = """
        \033[1;33m
               .-"``"-.
              /        \\
              |        |
              \  .--.  /
               |/    \|
               ||    ||
               ||    ||
               |\    /|
               \ '--' /
                `-..-'
                
               🐵 MONKEY GRAM 🐵
        \033[0m
        """
        print(monkey)
    
    def print_header(self, title: str):
        """Вывод заголовка раздела"""
        print("\n" + "═" * 60)
        print(f"\033[1;36m🐒 {title}\033[0m")
        print("═" * 60)
    
    def print_success(self, message: str):
        """Вывод успешного сообщения"""
        print(f"\033[1;32m✓ {message}\033[0m")
    
    def print_error(self, message: str):
        """Вывод сообщения об ошибке"""
        print(f"\033[1;31m✗ {message}\033[0m")
    
    def print_warning(self, message: str):
        """Вывод предупреждения"""
        print(f"\033[1;33m⚠ {message}\033[0m")
    
    def print_info(self, message: str):
        """Вывод информационного сообщения"""
        print(f"\033[1;34mℹ {message}\033[0m")
    
    def print_menu_item(self, number: str, text: str, emoji: str = ""):
        """Вывод пункта меню"""
        print(f"\033[1;37m{number}. {emoji} {text}\033[0m")
    
    async def load_config(self) -> Dict:
        """Загрузка конфигурации из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    async def save_config(self, config: Dict):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            self.print_error(f"Ошибка сохранения конфигурации: {e}")
    
    async def load_folders(self) -> Dict:
        """Загрузка папок для рассылки"""
        if os.path.exists(self.folders_file):
            try:
                with open(self.folders_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    async def save_folders(self, folders: Dict):
        """Сохранение папок для рассылки"""
        try:
            with open(self.folders_file, 'w', encoding='utf-8') as f:
                json.dump(folders, f, ensure_ascii=False, indent=2)
        except IOError as e:
            self.print_error(f"Ошибка сохранения папок: {e}")
    
    async def load_auto_reply(self) -> Dict:
        """Загрузка правил автоответчика"""
        if os.path.exists(self.auto_reply_file):
            try:
                with open(self.auto_reply_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"enabled": False, "rules": []}
        return {"enabled": False, "rules": []}
    
    async def save_auto_reply(self, auto_reply: Dict):
        """Сохранение правил автоответчика"""
        try:
            with open(self.auto_reply_file, 'w', encoding='utf-8') as f:
                json.dump(auto_reply, f, ensure_ascii=False, indent=2)
        except IOError as e:
            self.print_error(f"Ошибка сохранения правил автоответчика: {e}")
    
    async def load_accounts(self) -> Dict:
        """Загрузка аккаунтов"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"accounts": []}
        return {"accounts": []}
    
    async def save_accounts(self, accounts_data: Dict):
        """Сохранение аккаунтов"""
        try:
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(accounts_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            self.print_error(f"Ошибка сохранения аккаунтов: {e}")
    
    async def test_proxy(self, proxy_url: str) -> bool:
        """Тестирование прокси на работоспособность"""
        self.print_info(f"Тестирование прокси: {proxy_url}")
        
        try:
            # Пробуем подключиться через прокси
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                try:
                    # Пробуем получить IP через ipify
                    async with session.get('https://api.ipify.org?format=json', 
                                         proxy=proxy_url if '://' in proxy_url else None) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.print_success(f"Прокси работает! Ваш IP: {data.get('ip')}")
                            return True
                        else:
                            self.print_error(f"Ошибка HTTP: {response.status}")
                            return False
                except aiohttp.ClientError as e:
                    self.print_error(f"Ошибка подключения через прокси: {e}")
                    return False
                except Exception as e:
                    self.print_error(f"Неизвестная ошибка: {e}")
                    return False
                    
        except Exception as e:
            self.print_error(f"Ошибка тестирования прокси: {e}")
            return False
    
    async def create_account(self):
        """Создание нового аккаунта"""
        self.print_header("ДОБАВЛЕНИЕ НОВОГО АККАУНТА")
        
        accounts_data = await self.load_accounts()
        
        # Запрос имени аккаунта
        account_name = input("\n\033[1;37mВведите имя аккаунта (для идентификации): \033[0m").strip()
        while not account_name:
            self.print_error("Имя аккаунта не может быть пустым")
            account_name = input("\n\033[1;37mВведите имя аккаунта: \033[0m").strip()
        
        # Проверяем, нет ли уже аккаунта с таким именем
        for acc in accounts_data.get("accounts", []):
            if acc.get("name") == account_name:
                self.print_error(f"Аккаунт с именем '{account_name}' уже существует")
                return
        
        # Запрос API ID
        while True:
            try:
                api_id = input("\n\033[1;37mВведите API ID (получите на my.telegram.org): \033[0m").strip()
                api_id = int(api_id)
                break
            except ValueError:
                self.print_error("API ID должен быть целым числом")
        
        # Запрос API Hash
        api_hash = input("\n\033[1;37mВведите API Hash: \033[0m").strip()
        while not api_hash:
            self.print_error("API Hash не может быть пустым")
            api_hash = input("\n\033[1;37mВведите API Hash: \033[0m").strip()
        
        # Запрос номера телефона
        phone_number = input("\n\033[1;37mВведите номер телефона (с кодом страны): \033[0m").strip()
        while not phone_number:
            self.print_error("Номер телефона не может быть пустым")
            phone_number = input("\n\033[1;37mВведите номер телефона: \033[0m").strip()
        
        # Вопрос о прокси
        proxy_url = None
        use_proxy = input("\n\033[1;37mИспользовать прокси? (y/N): \033[0m").strip().lower()
        
        if use_proxy == 'y':
            proxy_url = input("\n\033[1;37mВведите URL прокси (формат: socks5://user:pass@host:port): \033[0m").strip()
            if proxy_url:
                self.print_info("Тестируем прокси...")
                if await self.test_proxy(proxy_url):
                    self.print_success("Прокси протестирован успешно!")
                else:
                    self.print_warning("Прокси не работает, продолжить без него?")
                    continue_without = input("\n\033[1;37mПродолжить без прокси? (y/N): \033[0m").strip().lower()
                    if continue_without != 'y':
                        return
                    proxy_url = None
            else:
                self.print_info("Продолжаем без прокси")
        
        # Создание сессии
        session_name = f"monkey_session_{account_name}"
        
        # Попытка авторизации
        try:
            client = Client(
                name=session_name,
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone_number,
                workdir="."
            )
            
            await client.connect()
            
            # Отправка кода
            try:
                sent_code = await client.send_code(phone_number)
                self.print_info(f"Код отправлен через: {sent_code.type.value}")
            except FloodWait as e:
                self.print_warning(f"Ожидайте {e.value} секунд перед повторной попыткой")
                await asyncio.sleep(e.value)
                sent_code = await client.send_code(phone_number)
            
            # Ввод кода
            code = input("\n\033[1;37mВведите код из SMS: \033[0m").strip()
            
            try:
                # Попытка входа с кодом
                await client.sign_in(
                    phone_number=phone_number,
                    phone_code_hash=sent_code.phone_code_hash,
                    phone_code=code
                )
            except SessionPasswordNeeded:
                # Запрос пароля 2FA
                password = input("\n\033[1;37mВведите пароль двухфакторной аутентификации: \033[0m").strip()
                await client.check_password(password)
            except (PhoneCodeInvalid, PhoneCodeExpired) as e:
                self.print_error(f"Ошибка: {e}")
                return False
            
            self.print_success("Авторизация успешна!")
            
            # Получаем информацию об аккаунте
            me = await client.get_me()
            
            # Сохраняем аккаунт
            new_account = {
                "name": account_name,
                "session_name": session_name,
                "api_id": api_id,
                "api_hash": api_hash,
                "phone_number": phone_number,
                "proxy_url": proxy_url,
                "user_id": me.id,
                "username": me.username or "",
                "first_name": me.first_name or "",
                "created_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat()
            }
            
            accounts_data.setdefault("accounts", []).append(new_account)
            await self.save_accounts(accounts_data)
            
            self.print_success(f"Аккаунт '{account_name}' успешно создан и сохранен!")
            
            # Отключаем клиента
            await client.disconnect()
            
            return True
            
        except Exception as e:
            self.print_error(f"Ошибка создания аккаунта: {e}")
            return False
    
    async def select_account(self):
        """Выбор аккаунта для работы"""
        accounts_data = await self.load_accounts()
        accounts = accounts_data.get("accounts", [])
        
        if not accounts:
            self.print_warning("Нет сохраненных аккаунтов")
            return None
        
        self.print_header("ВЫБОР АККАУНТА")
        
        for idx, account in enumerate(accounts, 1):
            proxy_info = "с прокси" if account.get("proxy_url") else "без прокси"
            print(f"\033[1;37m{idx:2}. {account['name']} (@{account.get('username', 'нет')}) - {proxy_info}\033[0m")
            print(f"    📞 {account['phone_number']}")
        
        print("\n" + "-" * 60)
        self.print_menu_item("0", "Добавить новый аккаунт", "➕")
        
        while True:
            try:
                choice = input("\n\033[1;37mВыберите аккаунт (номер): \033[0m").strip()
                
                if choice == "0":
                    await self.create_account()
                    accounts_data = await self.load_accounts()
                    accounts = accounts_data.get("accounts", [])
                    if not accounts:
                        return None
                    # Показываем обновленный список
                    return await self.select_account()
                
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(accounts):
                    selected_account = accounts[choice_idx - 1]
                    
                    # Обновляем время последнего входа
                    selected_account["last_login"] = datetime.now().isoformat()
                    accounts[choice_idx - 1] = selected_account
                    accounts_data["accounts"] = accounts
                    await self.save_accounts(accounts_data)
                    
                    self.print_success(f"Выбран аккаунт: {selected_account['name']}")
                    return selected_account
                else:
                    self.print_error("Неверный номер аккаунта")
                    
            except ValueError:
                self.print_error("Введите число")
            except Exception as e:
                self.print_error(f"Ошибка выбора аккаунта: {e}")
                return None
    
    async def login_to_account(self, account: Dict):
        """Вход в выбранный аккаунт"""
        self.print_info(f"Вход в аккаунт: {account['name']}")
        
        try:
            # Создаем клиента с настройками из аккаунта
            client = Client(
                name=account["session_name"],
                api_id=account["api_id"],
                api_hash=account["api_hash"],
                phone_number=account["phone_number"],
                workdir="."
            )
            
            # Если есть прокси, настраиваем его
            if account.get("proxy_url"):
                try:
                    # Парсим прокси URL
                    proxy_parts = account["proxy_url"].split("://")
                    if len(proxy_parts) == 2:
                        scheme = proxy_parts[0]
                        auth_host = proxy_parts[1]
                        
                        # Проверяем есть ли авторизация
                        if "@" in auth_host:
                            auth, host_port = auth_host.split("@")
                            if ":" in auth:
                                username, password = auth.split(":", 1)
                            else:
                                username = auth
                                password = None
                        else:
                            host_port = auth_host
                            username = None
                            password = None
                        
                        if ":" in host_port:
                            host, port = host_port.split(":", 1)
                            port = int(port)
                        else:
                            host = host_port
                            port = 1080  # default SOCKS5 port
                        
                        # Настраиваем прокси для pyrogram
                        client.proxy = {
                            "scheme": scheme,
                            "hostname": host,
                            "port": port
                        }
                        
                        if username and password:
                            client.proxy["username"] = username
                            client.proxy["password"] = password
                            
                        self.print_info(f"Используется прокси: {host}:{port}")
                except Exception as e:
                    self.print_warning(f"Ошибка настройки прокси: {e}. Продолжаем без прокси")
            
            # Запускаем клиента
            await client.start()
            
            # Проверяем авторизацию
            me = await client.get_me()
            self.print_success(f"Успешный вход! Привет, {me.first_name}!")
            
            # Сохраняем клиента
            self.client = client
            self.current_account = account
            
            return True
            
        except Exception as e:
            self.print_error(f"Ошибка входа в аккаунт: {e}")
            return False
    
    async def show_account_stats(self):
        """Функция 1: Статистика аккаунта"""
        self.print_header("СТАТИСТИКА АККАУНТА")
        
        if not self.client:
            self.print_error("Клиент не инициализирован")
            return
        
        try:
            me = await self.client.get_me()
            
            # Получаем полную информацию
            user_full = await self.client.get_users(me.id)
            
            # Получаем количество диалогов
            dialogs_count = 0
            try:
                async for _ in self.client.get_dialogs():
                    dialogs_count += 1
                    if dialogs_count % 20 == 0:
                        await asyncio.sleep(0.1)
            except:
                pass
            
            # Форматируем вывод
            print(f"\n\033[1;37m{'='*50}\033[0m")
            print(f"\033[1;36m👤 Основная информация:\033[0m")
            print(f"\033[1;37m{'─'*50}\033[0m")
            print(f"\033[1;33mID:\033[0m {me.id}")
            print(f"\033[1;33mИмя:\033[0m {me.first_name} {me.last_name or ''}")
            print(f"\033[1;33mUsername:\033[0m @{me.username if me.username else 'не установлен'}")
            print(f"\033[1;33mНомер:\033[0m {me.phone_number or 'скрыт'}")
            
            print(f"\n\033[1;36m📊 Статус и информация:\033[0m")
            print(f"\033[1;37m{'─'*50}\033[0m")
            status = user_full.status.value if user_full.status else "неизвестно"
            print(f"\033[1;33mСтатус:\033[0m {status}")
            print(f"\033[1;33mПремиум:\033[0m {'✅ Да' if me.is_premium else '❌ Нет'}")
            print(f"\033[1;33mВерифицирован:\033[0m {'✅ Да' if me.is_verified else '❌ Нет'}")
            print(f"\033[1;33mОграничен:\033[0m {'⚠️ Да' if me.is_restricted else '✅ Нет'}")
            
            print(f"\n\033[1;36m📈 Активность:\033[0m")
            print(f"\033[1;37m{'─'*50}\033[0m")
            print(f"\033[1;33mДиалогов:\033[0m {dialogs_count}")
            
            if self.current_account:
                print(f"\033[1;33mПрокси:\033[0m {'✅ Используется' if self.current_account.get('proxy_url') else '❌ Не используется'}")
                created = datetime.fromisoformat(self.current_account['created_at'].replace('Z', '+00:00'))
                print(f"\033[1;33mСоздан в MG:\033[0m {created.strftime('%d.%m.%Y %H:%M')}")
            
            print(f"\n\033[1;37m{'='*50}\033[0m")
            
        except Exception as e:
            self.print_error(f"Ошибка получения статистики: {e}")
    
    async def get_dialogs_list(self):
        """Получение списка диалогов"""
        self.print_info("Получение списка диалогов...")
        dialogs = []
        count = 0
        
        try:
            async for dialog in self.client.get_dialogs():
                chat = dialog.chat
                
                # Формируем имя чата
                if hasattr(chat, 'title') and chat.title:
                    name = chat.title
                elif hasattr(chat, 'first_name') and chat.first_name:
                    name = f"{chat.first_name} {chat.last_name or ''}".strip()
                else:
                    name = f"Chat {chat.id}"
                
                # Добавляем username если есть
                if hasattr(chat, 'username') and chat.username:
                    name += f" (@{chat.username})"
                
                dialogs.append({
                    'index': count + 1,
                    'id': chat.id,
                    'name': name,
                    'type': chat.type.value if hasattr(chat, 'type') else 'unknown'
                })
                
                count += 1
                
                # Пауза для избежания флуда
                if count % 10 == 0:
                    await asyncio.sleep(0.5)
                
                # Ограничиваем для демонстрации
                if count >= 50:
                    break
            
            return dialogs
        except Exception as e:
            self.print_error(f"Ошибка получения диалогов: {e}")
            return []
    
    async def create_mailing_folder(self):
        """Создание новой папки для рассылки"""
        self.print_header("СОЗДАНИЕ НОВОЙ ПАПКИ")
        
        # Запрос названия папки
        folder_name = input("\n\033[1;37mВведите название папки: \033[0m").strip()
        while not folder_name:
            self.print_error("Название папки не может быть пустым")
            folder_name = input("\n\033[1;37mВведите название папки: \033[0m").strip()
        
        # Получение списка диалогов
        dialogs = await self.get_dialogs_list()
        
        if not dialogs:
            self.print_error("Не удалось получить список диалогов")
            return None
        
        # Показать диалоги
        print(f"\n\033[1;36m📋 Список доступных чатов (первые {len(dialogs)}):\033[0m")
        print("\033[1;37m" + "─" * 50 + "\033[0m")
        for dialog in dialogs:
            print(f"\033[1;37m{dialog['index']:3}. {dialog['name']} \033[1;90m[{dialog['type']}]\033[0m")
        
        # Выбор чатов
        self.print_header("ВЫБОР ЧАТОВ ДЛЯ ПАПКИ")
        print("Введите номера чатов через пробел (максимум 20)")
        print("Пример: 1 3 5 7 10")
        print("Для выбора всех чатов введите: all")
        
        while True:
            try:
                selection = input("\n\033[1;37mВаш выбор: \033[0m").strip().lower()
                
                if not selection:
                    self.print_info("Отменено")
                    return None
                
                selected_chats = []
                
                if selection == "all":
                    # Выбираем все чаты
                    for dialog in dialogs:
                        selected_chats.append({
                            'id': dialog['id'],
                            'name': dialog['name']
                        })
                    self.print_info(f"Выбраны все {len(dialogs)} чатов")
                else:
                    # Парсинг выбора
                    selected_indices = list(map(int, selection.split()))
                    
                    # Проверка количества
                    if len(selected_indices) > 20:
                        self.print_error("Можно выбрать не более 20 чатов")
                        continue
                    
                    # Проверка валидности индексов
                    valid = True
                    for idx in selected_indices:
                        if idx < 1 or idx > len(dialogs):
                            self.print_error(f"Индекс {idx} вне диапазона")
                            valid = False
                            break
                    
                    if not valid:
                        continue
                    
                    # Получение выбранных чатов
                    for idx in selected_indices:
                        dialog = dialogs[idx - 1]
                        selected_chats.append({
                            'id': dialog['id'],
                            'name': dialog['name']
                        })
                
                # Сохранение папки
                folders = await self.load_folders()
                
                # Если папка уже существует
                if folder_name in folders:
                    overwrite = input(f"\n\033[1;37mПапка '{folder_name}' уже существует. Перезаписать? (y/N): \033[0m").strip().lower()
                    if overwrite != 'y':
                        self.print_info("Отменено")
                        return None
                
                folders[folder_name] = {
                    'created_at': datetime.now().isoformat(),
                    'chats': selected_chats,
                    'chat_count': len(selected_chats)
                }
                
                await self.save_folders(folders)
                
                self.print_success(f"Папка '{folder_name}' создана!")
                self.print_info(f"Добавлено чатов: {len(selected_chats)}")
                
                return folder_name
                
            except ValueError:
                self.print_error("Вводите только числа через пробел")
            except Exception as e:
                self.print_error(f"Ошибка: {e}")
    
    async def select_mailing_folder(self):
        """Выбор существующей папки"""
        folders = await self.load_folders()
        
        if not folders:
            self.print_warning("У вас нет созданных папок")
            return None
        
        self.print_header("ВЫБОР ПАПКИ ДЛЯ РАССЫЛКИ")
        
        folder_list = list(folders.keys())
        for idx, folder_name in enumerate(folder_list, 1):
            folder_data = folders[folder_name]
            print(f"\033[1;37m{idx:2}. {folder_name} \033[1;90m({folder_data['chat_count']} чатов)\033[0m")
        
        while True:
            try:
                choice = input("\n\033[1;37mВыберите папку (номер): \033[0m").strip()
                if not choice:
                    return None
                
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(folder_list):
                    selected_folder = folder_list[choice_idx - 1]
                    self.print_success(f"Выбрана папка: {selected_folder}")
                    return selected_folder
                else:
                    self.print_error("Неверный номер папки")
                    
            except ValueError:
                self.print_error("Введите число")
            except Exception as e:
                self.print_error(f"Ошибка: {e}")
                return None
    
    async def start_mailing(self, folder_name: str, message: str, 
                           message_count: int, delay: int):
        """Запуск рассылки сообщений"""
        folders = await self.load_folders()
        
        if folder_name not in folders:
            self.print_error(f"Папка '{folder_name}' не найдена")
            return False
        
        folder_data = folders[folder_name]
        chats = folder_data['chats']
        
        self.print_header("ЗАПУСК РАССЫЛКИ")
        print(f"\033[1;33m📁 Папка:\033[0m {folder_name}")
        print(f"\033[1;33m📝 Сообщений на чат:\033[0m {message_count}")
        print(f"\033[1;33m⏱️ Задержка между сообщениями:\033[0m {delay} сек")
        print(f"\033[1;33m👥 Всего чатов:\033[0m {len(chats)}")
        print(f"\033[1;33m📨 Всего сообщений:\033[0m {len(chats) * message_count}")
        print("\033[1;37m" + "─" * 50 + "\033[0m")
        
        confirm = input("\n\033[1;37mПодтвердите запуск рассылки (y/N): \033[0m").strip().lower()
        if confirm != 'y':
            self.print_info("Отменено")
            return False
        
        total_sent = 0
        total_failed = 0
        start_time = time.time()
        
        try:
            for chat_idx, chat in enumerate(chats, 1):
                print(f"\n\033[1;36m💬 Чат {chat_idx}/{len(chats)}: {chat['name']}\033[0m")
                
                for msg_idx in range(1, message_count + 1):
                    try:
                        await self.client.send_message(
                            chat_id=chat['id'],
                            text=message
                        )
                        
                        total_sent += 1
                        print(f"  \033[1;32m✓ Сообщение {msg_idx}/{message_count} отправлено\033[0m")
                        
                        # Пауза между сообщениями
                        if msg_idx < message_count:
                            print(f"  \033[1;34m⏳ Ожидание {delay} секунд...\033[0m")
                            await asyncio.sleep(delay)
                            
                    except FloodWait as e:
                        print(f"  \033[1;33m⚠ Флуд-контроль: ожидание {e.value} секунд\033[0m")
                        await asyncio.sleep(e.value)
                        
                        # Повторная попытка
                        try:
                            await self.client.send_message(
                                chat_id=chat['id'],
                                text=message
                            )
                            total_sent += 1
                            print(f"  \033[1;32m✓ Сообщение {msg_idx}/{message_count} отправлено (после ожидания)\033[0m")
                        except Exception as retry_error:
                            print(f"  \033[1;31m✗ Ошибка после ожидания: {retry_error}\033[0m")
                            total_failed += 1
                            
                    except RPCError as e:
                        print(f"  \033[1;31m✗ Ошибка отправки: {e}\033[0m")
                        total_failed += 1
                        break  # Переходим к следующему чату
                    except Exception as e:
                        print(f"  \033[1;31m✗ Неизвестная ошибка: {e}\033[0m")
                        total_failed += 1
                        break
                
                # Пауза между чатами
                if chat_idx < len(chats):
                    print(f"\n\033[1;34m⏳ Переход к следующему чату через 2 секунды...\033[0m")
                    await asyncio.sleep(2)
            
            elapsed_time = time.time() - start_time
            self.print_header("РАССЫЛКА ЗАВЕРШЕНА")
            print(f"\033[1;32m✅ Успешно отправлено:\033[0m {total_sent}")
            print(f"\033[1;31m❌ Не удалось отправить:\033[0m {total_failed}")
            print(f"\033[1;33m⏱️ Затраченное время:\033[0m {elapsed_time:.2f} секунд")
            if total_sent > 0:
                print(f"\033[1;33m📊 Скорость:\033[0m {total_sent/elapsed_time:.2f} сообщ/сек")
            
            return True
            
        except KeyboardInterrupt:
            self.print_warning("\n\nРассылка прервана пользователем")
            print(f"\033[1;33m📨 Успешно отправлено:\033[0m {total_sent}")
            return False
        except Exception as e:
            self.print_error(f"\nКритическая ошибка рассылки: {e}")
            return False
    
    async def mailing_menu(self):
        """Меню рассылки сообщений"""
        while True:
            self.print_header("МЕНЮ РАССЫЛКИ СООБЩЕНИЙ")
            self.print_menu_item("1", "Задать количество сообщений (1-1000)", "📊")
            self.print_menu_item("2", "Задать задержку между сообщениями (10-3000 сек)", "⏱️")
            self.print_menu_item("3", "Ввести текст сообщения", "📝")
            self.print_menu_item("4", "Управление папками", "📁")
            self.print_menu_item("5", "Запустить рассылку", "🚀")
            self.print_menu_item("6", "Вернуться в главное меню", "↩️")
            print("═" * 60)
            
            choice = input("\n\033[1;37mВыберите действие: \033[0m").strip()
            
            if choice == '1':
                # Количество сообщений
                try:
                    count = input("\n\033[1;37mКоличество сообщений на чат (1-1000): \033[0m").strip()
                    count = int(count)
                    if 1 <= count <= 1000:
                        self.mailing_count = count
                        self.print_success(f"Установлено: {count} сообщений на чат")
                    else:
                        self.print_error("Число должно быть от 1 до 1000")
                except ValueError:
                    self.print_error("Введите число")
                    
            elif choice == '2':
                # Задержка между сообщениями
                try:
                    delay = input("\n\033[1;37mЗадержка между сообщениями в секундах (10-3000): \033[0m").strip()
                    delay = int(delay)
                    if 10 <= delay <= 3000:
                        self.mailing_delay = delay
                        self.print_success(f"Установлено: задержка {delay} секунд")
                    else:
                        self.print_error("Число должно быть от 10 до 3000")
                except ValueError:
                    self.print_error("Введите число")
                    
            elif choice == '3':
                # Текст сообщения
                message = input("\n\033[1;37mВведите текст сообщения: \033[0m").strip()
                if message:
                    self.mailing_message = message
                    self.print_success("Текст сообщения сохранен")
                    print(f"\n\033[1;90mПредпросмотр: {message[:100]}{'...' if len(message) > 100 else ''}\033[0m")
                else:
                    self.print_error("Текст не может быть пустым")
                    
            elif choice == '4':
                # Управление папками
                self.print_header("УПРАВЛЕНИЕ ПАПКАМИ")
                self.print_menu_item("1", "Создать новую папку", "📁")
                self.print_menu_item("2", "Выбрать существующую папку", "📂")
                self.print_menu_item("3", "Просмотреть содержимое папки", "👁️")
                self.print_menu_item("4", "Удалить папку", "🗑️")
                self.print_menu_item("5", "Вернуться", "↩️")
                
                folder_choice = input("\n\033[1;37mВыберите действие: \033[0m").strip()
                
                if folder_choice == '1':
                    folder_name = await self.create_mailing_folder()
                    if folder_name:
                        self.selected_folder = folder_name
                        
                elif folder_choice == '2':
                    folder_name = await self.select_mailing_folder()
                    if folder_name:
                        self.selected_folder = folder_name
                        
                elif folder_choice == '3':
                    if hasattr(self, 'selected_folder') and self.selected_folder:
                        folders = await self.load_folders()
                        if self.selected_folder in folders:
                            folder_data = folders[self.selected_folder]
                            print(f"\n\033[1;36m📁 Папка:\033[0m {self.selected_folder}")
                            print(f"\033[1;33m📅 Создана:\033[0m {folder_data['created_at'][:10]}")
                            print(f"\033[1;33m👥 Количество чатов:\033[0m {folder_data['chat_count']}")
                            print(f"\n\033[1;36m📋 Список чатов:\033[0m")
                            for idx, chat in enumerate(folder_data['chats'], 1):
                                print(f"  \033[1;37m{idx:3}. {chat['name']}\033[0m")
                        else:
                            self.print_error("Папка не найдена")
                    else:
                        self.print_warning("Папка не выбрана")
                        
                elif folder_choice == '4':
                    folder_name = await self.select_mailing_folder()
                    if folder_name:
                        confirm = input(f"\n\033[1;37mУдалить папку '{folder_name}'? (y/N): \033[0m").strip().lower()
                        if confirm == 'y':
                            folders = await self.load_folders()
                            if folder_name in folders:
                                del folders[folder_name]
                                await self.save_folders(folders)
                                self.print_success(f"Папка '{folder_name}' удалена")
                                
                                if hasattr(self, 'selected_folder') and self.selected_folder == folder_name:
                                    del self.selected_folder
                        else:
                            self.print_info("Отменено")
                            
            elif choice == '5':
                # Запуск рассылки
                if not hasattr(self, 'mailing_message') or not self.mailing_message:
                    self.print_error("Не задан текст сообщения")
                    continue
                    
                if not hasattr(self, 'selected_folder') or not self.selected_folder:
                    self.print_error("Не выбрана папка")
                    continue
                    
                if not hasattr(self, 'mailing_count'):
                    self.mailing_count = 1
                    
                if not hasattr(self, 'mailing_delay'):
                    self.mailing_delay = 10
                
                await self.start_mailing(
                    folder_name=self.selected_folder,
                    message=self.mailing_message,
                    message_count=self.mailing_count,
                    delay=self.mailing_delay
                )
                
            elif choice == '6':
                break
                
            else:
                self.print_error("Неверный выбор")
    
    async def check_spam_block(self):
        """Функция 3: Проверка спам-блока"""
        self.print_header("ПРОВЕРКА СПАМ-БЛОКА")
        
        try:
            # Поиск SpamBot
            self.print_info("Поиск @SpamBot...")
            try:
                spam_bot = await self.client.get_users("spambot")
            except:
                self.print_error("Не удалось найти @SpamBot")
                return
            
            # Отправка /start
            self.print_info("Отправка команды /start...")
            await self.client.send_message(spam_bot.id, "/start")
            
            # Ожидание ответа
            self.print_info("Ожидание ответа...")
            await asyncio.sleep(5)
            
            # Получение истории сообщений
            messages = []
            async for message in self.client.get_chat_history(spam_bot.id, limit=5):
                if message.from_user and message.from_user.id == spam_bot.id:
                    messages.append(message)
            
            if messages:
                latest_message = messages[0]
                self.print_header("ОТВЕТ ОТ @SPAMBOT")
                if latest_message.text:
                    # Выделяем важную информацию цветом
                    text = latest_message.text
                    if "ограничений" in text.lower() or "ограничен" in text.lower():
                        text = f"\033[1;31m{text}\033[0m"
                    elif "нет ограничений" in text.lower():
                        text = f"\033[1;32m{text}\033[0m"
                    print(text)
                elif latest_message.caption:
                    print(latest_message.caption)
                else:
                    self.print_warning("Сообщение не содержит текста")
            else:
                self.print_error("Не удалось получить ответ от @SpamBot")
                
        except FloodWait as e:
            self.print_warning(f"Флуд-контроль: ожидание {e.value} секунд")
            await asyncio.sleep(e.value)
        except Exception as e:
            self.print_error(f"Ошибка проверки спам-блока: {e}")
    
    async def handle_button_click(self, message: types.Message):
        """Обработка нажатия кнопок в сообщениях"""
        try:
            # Проверка наличия кнопок
            has_buttons = False
            button_to_click = None
            
            if message.reply_markup:
                # Проверяем разные типы клавиатур
                if isinstance(message.reply_markup, types.ReplyKeyboardMarkup):
                    if message.reply_markup.keyboard:
                        has_buttons = True
                        # Первая кнопка первой строки
                        button_to_click = message.reply_markup.keyboard[0][0]
                        
                elif isinstance(message.reply_markup, types.InlineKeyboardMarkup):
                    if message.reply_markup.inline_keyboard:
                        has_buttons = True
                        # Первая кнопка
                        button_to_click = message.reply_markup.inline_keyboard[0][0]
            
            if has_buttons and button_to_click:
                chat_title = message.chat.title if hasattr(message.chat, 'title') else 'Unknown'
                print(f"\n\033[1;36m🎯 Найдены кнопки в сообщении от {chat_title}\033[0m")
                print(f"\033[1;33mТекст кнопки:\033[0m {button_to_click.text}")
                
                # Для ReplyKeyboardMarkup просто отправляем текст кнопки
                if isinstance(button_to_click, types.KeyboardButton):
                    await self.client.send_message(
                        chat_id=message.chat.id,
                        text=button_to_click.text
                    )
                    print(f"\033[1;32m✓ Отправлен текст кнопки: {button_to_click.text}\033[0m")
                    return True
                
                # Для InlineKeyboardMarkup
                elif isinstance(button_to_click, types.InlineKeyboardButton):
                    if button_to_click.url:
                        print(f"\033[1;34m🔗 Ссылка: {button_to_click.url}\033[0m")
                        print("\033[1;33mℹ Для перехода по ссылке нужно нажать кнопку вручную\033[0m")
                        return True
                    elif button_to_click.callback_data:
                        # Отправляем callback запрос
                        try:
                            await self.client.request_callback_answer(
                                chat_id=message.chat.id,
                                message_id=message.id,
                                callback_data=button_to_click.callback_data
                            )
                            print(f"\033[1;32m✓ Нажата inline-кнопка: {button_to_click.text}\033[0m")
                            return True
                        except Exception as e:
                            print(f"\033[1;31m✗ Ошибка нажатия inline-кнопки: {e}\033[0m")
                            return False
                    else:
                        print("\033[1;33m⚠ Неизвестный тип inline-кнопки\033[0m")
                        return False
                
        except Exception as e:
            self.print_error(f"Ошибка обработки кнопок: {e}")
        
        return False
    
    async def start_auto_subscribe(self):
        """Запуск авто-подписки"""
        self.print_header("АВТО-ПОДПИСКА")
        print("\033[1;33m🤖 Бот будет мониторить ответы на ваши сообщения")
        print("и автоматически нажимать кнопки подписки\033[0m")
        print("\n\033[1;31m⚠ Для остановки нажмите Ctrl+C\033[0m")
        
        self.auto_subscribe_running = True
        self.stop_event.clear()
        
        # Создаем обработчик сообщений
        @self.client.on_message(filters.reply)
        async def reply_handler(client, message):
            try:
                # Проверяем, что авто-подписка активна
                if not self.auto_subscribe_running:
                    return
                
                # Проверяем, что это ответ на наше сообщение
                if message.reply_to_message:
                    # Получаем оригинальное сообщение
                    original_msg = message.reply_to_message
                    
                    # Проверяем, что оригинальное сообщение от нас
                    me = await client.get_me()
                    if original_msg.from_user and original_msg.from_user.id == me.id:
                        chat_title = message.chat.title if hasattr(message.chat, 'title') else 'Unknown'
                        print(f"\n\033[1;36m📨 Получен ответ на ваше сообщение в чате: {chat_title}\033[0m")
                        
                        # Ожидаем немного, чтобы сообщение полностью обработалось
                        await asyncio.sleep(1)
                        
                        # Проверяем кнопки в ответном сообщении
                        await self.handle_button_click(message)
            
            except Exception as e:
                self.print_error(f"Ошибка обработки ответа: {e}")
        
        try:
            # Регистрируем обработчик
            self.client.add_handler(reply_handler)
            
            # Бесконечный цикл с проверкой stop_event
            while self.auto_subscribe_running and not self.stop_event.is_set():
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.print_warning("\n\nАвто-подписка остановлена пользователем")
        except Exception as e:
            self.print_error(f"\nОшибка в авто-подписке: {e}")
        finally:
            self.auto_subscribe_running = False
            # Удаляем обработчик
            self.client.remove_handler(reply_handler)
            self.print_success("Авто-подписка выключена")
    
    async def manage_auto_reply(self):
        """Управление автоответчиком"""
        auto_reply = await self.load_auto_reply()
        
        while True:
            self.print_header("УПРАВЛЕНИЕ АВТООТВЕТЧИКОМ")
            status = "ВКЛЮЧЕН" if auto_reply.get('enabled') else "ВЫКЛЮЧЕН"
            status_color = "\033[1;32m" if auto_reply.get('enabled') else "\033[1;31m"
            print(f"Статус: {status_color}{status}\033[0m")
            print(f"Правил: \033[1;36m{len(auto_reply.get('rules', []))}\033[0m")
            print("═" * 60)
            
            self.print_menu_item("1", "Включить/выключить автоответчик", "🔌")
            self.print_menu_item("2", "Добавить правило", "➕")
            self.print_menu_item("3", "Удалить правило", "🗑️")
            self.print_menu_item("4", "Просмотреть правила", "👁️")
            self.print_menu_item("5", "Запустить автоответчик", "🤖")
            self.print_menu_item("6", "Вернуться в главное меню", "↩️")
            print("═" * 60)
            
            choice = input("\n\033[1;37mВыберите действие: \033[0m").strip()
            
            if choice == '1':
                # Включение/выключение
                auto_reply['enabled'] = not auto_reply.get('enabled', False)
                await self.save_auto_reply(auto_reply)
                status = "включен" if auto_reply['enabled'] else "выключен"
                status_color = "\033[1;32m" if auto_reply['enabled'] else "\033[1;31m"
                self.print_success(f"Автоответчик {status_color}{status}\033[1;32m")
                
            elif choice == '2':
                # Добавление правила
                self.print_header("ДОБАВЛЕНИЕ НОВОГО ПРАВИЛА")
                
                keyword = input("\n\033[1;37mКлючевое слово или фраза (или * для всех сообщений): \033[0m").strip()
                if not keyword:
                    self.print_error("Ключевое слово не может быть пустым")
                    continue
                
                response = input("\n\033[1;37mОтвет на сообщение: \033[0m").strip()
                if not response:
                    self.print_error("Ответ не может быть пустым")
                    continue
                
                # Проверяем существование правила
                existing = False
                for rule in auto_reply.get('rules', []):
                    if rule.get('keyword') == keyword:
                        existing = True
                        break
                
                if existing:
                    overwrite = input(f"\n\033[1;37mПравило для '{keyword}' уже существует. Перезаписать? (y/N): \033[0m").strip().lower()
                    if overwrite != 'y':
                        self.print_info("Отменено")
                        continue
                    # Удаляем старое правило
                    auto_reply['rules'] = [r for r in auto_reply.get('rules', []) if r.get('keyword') != keyword]
                
                # Добавляем новое правило
                new_rule = {
                    'keyword': keyword,
                    'response': response,
                    'created_at': datetime.now().isoformat()
                }
                
                if 'rules' not in auto_reply:
                    auto_reply['rules'] = []
                
                auto_reply['rules'].append(new_rule)
                await self.save_auto_reply(auto_reply)
                
                self.print_success(f"Правило добавлено: '{keyword}' -> '{response}'")
                
            elif choice == '3':
                # Удаление правила
                if not auto_reply.get('rules'):
                    self.print_error("Нет правил для удаления")
                    continue
                
                print(f"\n\033[1;36m📋 Список правил:\033[0m")
                for idx, rule in enumerate(auto_reply['rules'], 1):
                    print(f"\033[1;37m{idx}. '{rule['keyword']}' -> '{rule['response']}'\033[0m")
                
                try:
                    rule_num = input("\n\033[1;37mНомер правила для удаления: \033[0m").strip()
                    rule_num = int(rule_num)
                    if 1 <= rule_num <= len(auto_reply['rules']):
                        removed = auto_reply['rules'].pop(rule_num - 1)
                        await self.save_auto_reply(auto_reply)
                        self.print_success(f"Правило удалено: '{removed['keyword']}'")
                    else:
                        self.print_error("Неверный номер правила")
                except ValueError:
                    self.print_error("Введите число")
                    
            elif choice == '4':
                # Просмотр правил
                self.print_header("СПИСОК ПРАВИЛ АВТООТВЕТЧИКА")
                
                if not auto_reply.get('rules'):
                    self.print_warning("Правил нет")
                else:
                    for idx, rule in enumerate(auto_reply['rules'], 1):
                        print(f"\n\033[1;36m{idx}. Правило:\033[0m")
                        print(f"   \033[1;33mКлючевое слово:\033[0m '{rule['keyword']}'")
                        print(f"   \033[1;33mОтвет:\033[0m '{rule['response']}'")
                        print(f"   \033[1;90mСоздано: {rule['created_at'][:19]}\033[0m")
                        print("\033[1;90m" + "─" * 30 + "\033[0m")
                
            elif choice == '5':
                # Запуск автоответчика
                if not auto_reply.get('rules'):
                    self.print_error("Нет правил для автоответчика")
                    continue
                
                if not auto_reply.get('enabled', False):
                    self.print_error("Автоответчик выключен. Включите его в настройках.")
                    continue
                
                await self.start_auto_reply()
                
            elif choice == '6':
                break
                
            else:
                self.print_error("Неверный выбор")
    
    async def start_auto_reply(self):
        """Запуск автоответчика"""
        auto_reply = await self.load_auto_reply()
        
        self.print_header("АВТООТВЕТЧИК ЗАПУЩЕН")
        print(f"\033[1;36m📊 Количество правил: {len(auto_reply['rules'])}\033[0m")
        print("\033[1;33m🤖 Автоответчик будет отвечать на входящие сообщения\033[0m")
        print("\n\033[1;31m⚠ Для остановки нажмите Ctrl+C\033[0m")
        
        self.auto_reply_running = True
        self.stop_event.clear()
        processed_messages = set()  # Для избежания повторной обработки
        
        # Обработчик входящих сообщений
        @self.client.on_message(filters.private & filters.incoming)
        async def message_handler(client, message):
            try:
                # Проверяем, что автоответчик активен
                if not self.auto_reply_running:
                    return
                
                # Проверяем, что это не наше сообщение
                me = await client.get_me()
                if message.from_user and message.from_user.id == me.id:
                    return
                
                # Проверяем, не обрабатывали ли мы уже это сообщение
                message_id = f"{message.chat.id}_{message.id}"
                if message_id in processed_messages:
                    return
                
                processed_messages.add(message_id)
                
                # Очистка старых ID (чтобы не накапливались)
                if len(processed_messages) > 1000:
                    # Оставляем только последние 500
                    processed_messages.clear()
                
                # Получаем текст сообщения
                text = message.text or message.caption or ""
                
                sender_name = message.from_user.first_name if message.from_user else 'Unknown'
                print(f"\n\033[1;36m📩 Новое сообщение от {sender_name}:\033[0m")
                print(f"\033[1;37m   Текст: {text[:100]}{'...' if len(text) > 100 else ''}\033[0m")
                
                # Ищем подходящее правило
                response_text = None
                
                for rule in auto_reply.get('rules', []):
                    keyword = rule['keyword']
                    
                    # Если ключевое слово "*", отвечаем на все
                    if keyword == "*":
                        response_text = rule['response']
                        break
                    
                    # Иначе ищем ключевое слово в тексте
                    if keyword.lower() in text.lower():
                        response_text = rule['response']
                        break
                
                # Если нашли подходящее правило
                if response_text:
                    # Задержка перед ответом (имитация человека)
                    await asyncio.sleep(1)
                    
                    try:
                        # Отправляем ответ
                        await message.reply(response_text)
                        print(f"\033[1;32m✓ Отправлен ответ: {response_text[:100]}{'...' if len(response_text) > 100 else ''}\033[0m")
                        
                        # Задержка между ответами
                        await asyncio.sleep(2)
                        
                    except FloodWait as e:
                        self.print_warning(f"Флуд-контроль: ждем {e.value} секунд")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        self.print_error(f"Ошибка отправки ответа: {e}")
                else:
                    print("\033[1;90m   ℹ Нет подходящего правила для ответа\033[0m")
                
            except Exception as e:
                self.print_error(f"Ошибка обработки сообщения: {e}")
        
        try:
            # Регистрируем обработчик
            self.client.add_handler(message_handler)
            
            # Бесконечный цикл с проверкой stop_event
            while self.auto_reply_running and not self.stop_event.is_set():
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.print_warning("\n\nАвтоответчик остановлен пользователем")
        except Exception as e:
            self.print_error(f"\nОшибка в автоответчике: {e}")
        finally:
            self.auto_reply_running = False
            # Удаляем обработчик
            self.client.remove_handler(message_handler)
            self.print_success("Автоответчик выключен")
    
    async def simple_functions_menu(self):
        """Меню простых функций"""
        while True:
            self.print_header("ПРОСТЫЕ ФУНКЦИИ")
            self.print_menu_item("1", "Проверить онлайн статус", "🟢")
            self.print_menu_item("2", "Сменить имя/фамилию", "👤")
            self.print_menu_item("3", "Сменить био", "📝")
            self.print_menu_item("4", "Скачать историю чата", "📥")
            self.print_menu_item("5", "Очистить историю чата", "🗑️")
            self.print_menu_item("6", "Проверить доступ к каналу", "🔍")
            self.print_menu_item("7", "Выйти из группы/канала", "🚪")
            self.print_menu_item("8", "Назад в главное меню", "↩️")
            print("═" * 60)
            
            choice = input("\n\033[1;37mВыберите функцию: \033[0m").strip()
            
            if choice == '1':
                await self.check_online_status()
            elif choice == '2':
                await self.change_name()
            elif choice == '3':
                await self.change_bio()
            elif choice == '4':
                await self.download_chat_history()
            elif choice == '5':
                await self.clear_chat_history()
            elif choice == '6':
                await self.check_channel_access()
            elif choice == '7':
                await self.leave_chat()
            elif choice == '8':
                break
            else:
                self.print_error("Неверный выбор")
    
    async def check_online_status(self):
        """Проверка онлайн статуса контактов"""
        self.print_header("ПРОВЕРКА ОНЛАЙН СТАТУСА")
        
        try:
            # Получаем список контактов
            contacts = []
            async for dialog in self.client.get_dialogs():
                if dialog.chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
                    user = await self.client.get_users(dialog.chat.id)
                    if user.status:
                        contacts.append({
                            'name': user.first_name or user.title or f"User {user.id}",
                            'status': user.status.value,
                            'last_online': getattr(user.status, 'date', None)
                        })
            
            if not contacts:
                self.print_warning("Нет контактов для проверки")
                return
            
            # Сортируем по статусу
            online = []
            offline = []
            for contact in contacts:
                if contact['status'] == 'online':
                    online.append(contact)
                else:
                    offline.append(contact)
            
            print(f"\n\033[1;32m🟢 В сети: {len(online)}\033[0m")
            for contact in online[:10]:  # Показываем первые 10
                print(f"   \033[1;37m{contact['name']}\033[0m")
            
            print(f"\n\033[1;90m⚫ Не в сети: {len(offline)}\033[0m")
            for contact in offline[:10]:  # Показываем первые 10
                last_seen = ""
                if contact['last_online']:
                    last_seen = contact['last_online'].strftime(" (%H:%M)")
                print(f"   \033[1;37m{contact['name']}{last_seen}\033[0m")
            
            if len(online) > 10 or len(offline) > 10:
                self.print_info(f"Показано 10 из {len(online)+len(offline)} контактов")
            
        except Exception as e:
            self.print_error(f"Ошибка проверки статуса: {e}")
    
    async def change_name(self):
        """Смена имени и фамилии"""
        self.print_header("СМЕНА ИМЕНИ И ФАМИЛИИ")
        
        try:
            me = await self.client.get_me()
            print(f"\n\033[1;33mТекущее имя:\033[0m {me.first_name} {me.last_name or ''}")
            
            new_first_name = input("\n\033[1;37mНовое имя (оставьте пустым чтобы не менять): \033[0m").strip()
            new_last_name = input("\n\033[1;37mНовая фамилия (оставьте пустым чтобы не менять): \033[0m").strip()
            
            if not new_first_name and not new_last_name:
                self.print_info("Имя не изменено")
                return
            
            await self.client.update_profile(
                first_name=new_first_name if new_first_name else me.first_name,
                last_name=new_last_name if new_last_name else (me.last_name or "")
            )
            
            self.print_success("Имя успешно изменено!")
            
        except Exception as e:
            self.print_error(f"Ошибка смены имени: {e}")
    
    async def change_bio(self):
        """Смена био (о себе)"""
        self.print_header("СМЕНА БИО")
        
        try:
            me = await self.client.get_me()
            user_full = await self.client.get_users(me.id)
            current_bio = user_full.bio or ""
            
            print(f"\n\033[1;33mТекущее био:\033[0m {current_bio}")
            
            new_bio = input("\n\033[1;37mНовое био (макс 70 символов, оставьте пустым чтобы удалить): \033[0m").strip()
            
            if len(new_bio) > 70:
                self.print_error("Био не должно превышать 70 символов")
                return
            
            await self.client.update_profile(bio=new_bio)
            
            if new_bio:
                self.print_success("Био успешно обновлено!")
            else:
                self.print_success("Био успешно удалено!")
            
        except Exception as e:
            self.print_error(f"Ошибка смены био: {e}")
    
    async def download_chat_history(self):
        """Скачивание истории чата"""
        self.print_header("СКАЧИВАНИЕ ИСТОРИИ ЧАТА")
        
        try:
            # Выбор чата
            dialogs = await self.get_dialogs_list()
            if not dialogs:
                self.print_error("Не удалось получить список диалогов")
                return
            
            print(f"\n\033[1;36mВыберите чат:\033[0m")
            for dialog in dialogs[:20]:  # Показываем первые 20
                print(f"\033[1;37m{dialog['index']:3}. {dialog['name']}\033[0m")
            
            try:
                choice = input("\n\033[1;37mНомер чата: \033[0m").strip()
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(dialogs[:20]):
                    selected_chat = dialogs[choice_idx - 1]
                else:
                    self.print_error("Неверный номер чата")
                    return
            except ValueError:
                self.print_error("Введите число")
                return
            
            # Запрос количества сообщений
            try:
                limit = input("\n\033[1;37mСколько сообщений скачать (1-1000): \033[0m").strip()
                limit = int(limit)
                if limit < 1 or limit > 1000:
                    self.print_error("Число должно быть от 1 до 1000")
                    return
            except ValueError:
                self.print_error("Введите число")
                return
            
            # Создаем папку для сохранения
            os.makedirs("chat_history", exist_ok=True)
            filename = f"chat_history/{selected_chat['name'].replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            self.print_info(f"Скачиваю историю чата {selected_chat['name']}...")
            
            messages = []
            async for message in self.client.get_chat_history(selected_chat['id'], limit=limit):
                # Форматируем сообщение
                time_str = message.date.strftime("%Y-%m-%d %H:%M:%S")
                sender = message.from_user.first_name if message.from_user else "Unknown"
                text = message.text or message.caption or "[Медиа]"
                
                messages.append(f"[{time_str}] {sender}: {text}")
                
                if len(messages) % 50 == 0:
                    print(f"  \033[1;34mСкачано: {len(messages)}/{limit}\033[0m")
                    await asyncio.sleep(0.1)
            
            # Сохраняем в файл
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"История чата: {selected_chat['name']}\n")
                f.write(f"Всего сообщений: {len(messages)}\n")
                f.write("=" * 50 + "\n\n")
                f.write("\n".join(reversed(messages)))  # В хронологическом порядке
            
            self.print_success(f"История сохранена в файл: {filename}")
            self.print_info(f"Скачано сообщений: {len(messages)}")
            
        except Exception as e:
            self.print_error(f"Ошибка скачивания истории: {e}")
    
    async def clear_chat_history(self):
        """Очистка истории чата"""
        self.print_header("ОЧИСТКА ИСТОРИИ ЧАТА")
        
        try:
            # Выбор чата
            dialogs = await self.get_dialogs_list()
            if not dialogs:
                self.print_error("Не удалось получить список диалогов")
                return
            
            print(f"\n\033[1;36mВыберите чат для очистки:\033[0m")
            for dialog in dialogs[:15]:  # Показываем первые 15
                print(f"\033[1;37m{dialog['index']:3}. {dialog['name']}\033[0m")
            
            try:
                choice = input("\n\033[1;37mНомер чата: \033[0m").strip()
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(dialogs[:15]):
                    selected_chat = dialogs[choice_idx - 1]
                else:
                    self.print_error("Неверный номер чата")
                    return
            except ValueError:
                self.print_error("Введите число")
                return
            
            # Подтверждение
            confirm = input(f"\n\033[1;31mВЫ УВЕРЕНЫ? Очистить историю чата '{selected_chat['name']}'? (y/N): \033[0m").strip().lower()
            if confirm != 'y':
                self.print_info("Отменено")
                return
            
            self.print_info("Очищаю историю...")
            
            # Удаляем сообщения
            deleted_count = 0
            async for message in self.client.get_chat_history(selected_chat['id']):
                try:
                    await message.delete()
                    deleted_count += 1
                    
                    if deleted_count % 10 == 0:
                        print(f"  \033[1;34mУдалено: {deleted_count} сообщений\033[0m")
                        await asyncio.sleep(0.5)
                    
                except Exception as e:
                    continue  # Пропускаем сообщения, которые не можем удалить
            
            self.print_success(f"Удалено сообщений: {deleted_count}")
            
        except Exception as e:
            self.print_error(f"Ошибка очистки истории: {e}")
    
    async def check_channel_access(self):
        """Проверка доступа к каналу"""
        self.print_header("ПРОВЕРКА ДОСТУПА К КАНАЛУ")
        
        try:
            channel_link = input("\n\033[1;37mВведите ссылку на канал (например: @channelname): \033[0m").strip()
            if not channel_link:
                self.print_error("Ссылка не может быть пустой")
                return
            
            try:
                # Пробуем получить информацию о канале
                chat = await self.client.get_chat(channel_link)
                
                print(f"\n\033[1;32m✅ Доступ к каналу есть!\033[0m")
                print(f"\033[1;33mНазвание:\033[0m {chat.title}")
                print(f"\033[1;33mУчастников:\033[0m {getattr(chat, 'members_count', 'Неизвестно')}")
                
                # Проверяем, подписан ли пользователь
                try:
                    member = await self.client.get_chat_member(chat.id, "me")
                    status = member.status.value
                    if status in ['member', 'administrator', 'creator']:
                        print(f"\033[1;32mСтатус:\033[0m Подписан ({status})")
                    else:
                        print(f"\033[1;33mСтатус:\033[0m Не подписан ({status})")
                except:
                    print(f"\033[1;33mСтатус:\033[0m Не подписан")
                
            except Exception as e:
                self.print_error(f"❌ Нет доступа к каналу или канал не найден: {e}")
                
        except Exception as e:
            self.print_error(f"Ошибка проверки доступа: {e}")
    
    async def leave_chat(self):
        """Выход из группы/канала"""
        self.print_header("ВЫХОД ИЗ ГРУППЫ/КАНАЛА")
        
        try:
            # Получаем только группы и каналы
            groups = []
            async for dialog in self.client.get_dialogs():
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                    groups.append({
                        'id': dialog.chat.id,
                        'name': dialog.chat.title or f"Chat {dialog.chat.id}",
                        'type': dialog.chat.type.value
                    })
            
            if not groups:
                self.print_warning("Вы не состоите в группах или каналах")
                return
            
            print(f"\n\033[1;36mВыберите чат для выхода:\033[0m")
            for idx, group in enumerate(groups[:20], 1):  # Показываем первые 20
                print(f"\033[1;37m{idx:3}. {group['name']} \033[1;90m[{group['type']}]\033[0m")
            
            try:
                choice = input("\n\033[1;37mНомер чата: \033[0m").strip()
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(groups[:20]):
                    selected_chat = groups[choice_idx - 1]
                else:
                    self.print_error("Неверный номер чата")
                    return
            except ValueError:
                self.print_error("Введите число")
                return
            
            # Подтверждение
            confirm = input(f"\n\033[1;31mВыйти из '{selected_chat['name']}'? (y/N): \033[0m").strip().lower()
            if confirm != 'y':
                self.print_info("Отменено")
                return
            
            try:
                await self.client.leave_chat(selected_chat['id'])
                self.print_success(f"Вы успешно вышли из '{selected_chat['name']}'")
            except Exception as e:
                self.print_error(f"Ошибка выхода из чата: {e}")
            
        except Exception as e:
            self.print_error(f"Ошибка: {e}")
    
    async def manage_accounts(self):
        """Управление аккаунтами"""
        while True:
            self.print_header("УПРАВЛЕНИЕ АККАУНТАМИ")
            
            accounts_data = await self.load_accounts()
            accounts = accounts_data.get("accounts", [])
            
            if accounts:
                print(f"\n\033[1;36m📊 Всего аккаунтов: {len(accounts)}\033[0m")
                print("\033[1;37m" + "─" * 50 + "\033[0m")
                
                for idx, account in enumerate(accounts, 1):
                    status = "✅" if account.get('session_name') and os.path.exists(f"{account['session_name']}.session") else "❌"
                    proxy = "🔗" if account.get('proxy_url') else "➖"
                    last_login = account.get('last_login', 'никогда')
                    if last_login != 'никогда':
                        try:
                            last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00')).strftime('%d.%m.%Y')
                        except:
                            pass
                    
                    print(f"\033[1;37m{idx:2}. {status} {account['name']} {proxy}")
                    print(f"    \033[1;90m📞 {account['phone_number']} | 📅 {last_login}\033[0m")
            else:
                self.print_warning("Нет сохраненных аккаунтов")
            
            print("\n" + "═" * 60)
            self.print_menu_item("1", "Добавить новый аккаунт", "➕")
            self.print_menu_item("2", "Удалить аккаунт", "🗑️")
            self.print_menu_item("3", "Изменить прокси аккаунта", "🔧")
            self.print_menu_item("4", "Экспорт аккаунтов в файл", "📤")
            self.print_menu_item("5", "Импорт аккаунтов из файла", "📥")
            self.print_menu_item("6", "Назад в главное меню", "↩️")
            print("═" * 60)
            
            choice = input("\n\033[1;37mВыберите действие: \033[0m").strip()
            
            if choice == '1':
                await self.create_account()
                
            elif choice == '2':
                if not accounts:
                    self.print_error("Нет аккаунтов для удаления")
                    continue
                
                try:
                    acc_num = input("\n\033[1;37mНомер аккаунта для удаления: \033[0m").strip()
                    acc_idx = int(acc_num)
                    if 1 <= acc_idx <= len(accounts):
                        account = accounts[acc_idx - 1]
                        confirm = input(f"\n\033[1;31mУдалить аккаунт '{account['name']}'? (y/N): \033[0m").strip().lower()
                        if confirm == 'y':
                            # Удаляем файл сессии если существует
                            session_file = f"{account['session_name']}.session"
                            if os.path.exists(session_file):
                                os.remove(session_file)
                            
                            # Удаляем аккаунт из списка
                            accounts.pop(acc_idx - 1)
                            accounts_data["accounts"] = accounts
                            await self.save_accounts(accounts_data)
                            
                            self.print_success(f"Аккаунт '{account['name']}' удален")
                        else:
                            self.print_info("Отменено")
                    else:
                        self.print_error("Неверный номер аккаунта")
                except ValueError:
                    self.print_error("Введите число")
                    
            elif choice == '3':
                if not accounts:
                    self.print_error("Нет аккаунтов")
                    continue
                
                try:
                    acc_num = input("\n\033[1;37mНомер аккаунта для изменения прокси: \033[0m").strip()
                    acc_idx = int(acc_num)
                    if 1 <= acc_idx <= len(accounts):
                        account = accounts[acc_idx - 1]
                        print(f"\n\033[1;33mТекущий прокси:\033[0m {account.get('proxy_url', 'не используется')}")
                        
                        new_proxy = input("\n\033[1;37mНовый прокси (оставьте пустым чтобы удалить, или введите новый): \033[0m").strip()
                        
                        if new_proxy:
                            # Тестируем новый прокси
                            self.print_info("Тестируем прокси...")
                            if await self.test_proxy(new_proxy):
                                account['proxy_url'] = new_proxy
                                accounts[acc_idx - 1] = account
                                accounts_data["accounts"] = accounts
                                await self.save_accounts(accounts_data)
                                self.print_success("Прокси успешно обновлен!")
                            else:
                                self.print_warning("Прокси не работает, не сохраняем")
                        else:
                            # Удаляем прокси
                            if 'proxy_url' in account:
                                del account['proxy_url']
                                accounts[acc_idx - 1] = account
                                accounts_data["accounts"] = accounts
                                await self.save_accounts(accounts_data)
                                self.print_success("Прокси удален")
                            else:
                                self.print_info("У аккаунта и так нет прокси")
                    else:
                        self.print_error("Неверный номер аккаунта")
                except ValueError:
                    self.print_error("Введите число")
                    
            elif choice == '4':
                # Экспорт аккаунтов
                if not accounts:
                    self.print_error("Нет аккаунтов для экспорта")
                    continue
                
                filename = f"monkey_accounts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(accounts_data, f, ensure_ascii=False, indent=2)
                
                self.print_success(f"Аккаунты экспортированы в файл: {filename}")
                self.print_info(f"Всего экспортировано аккаунтов: {len(accounts)}")
                
            elif choice == '5':
                # Импорт аккаунтов
                filename = input("\n\033[1;37mИмя файла для импорта (monkey_accounts_export_*.json): \033[0m").strip()
                if not os.path.exists(filename):
                    self.print_error(f"Файл {filename} не найден")
                    continue
                
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        import_data = json.load(f)
                    
                    if 'accounts' not in import_data:
                        self.print_error("Некорректный формат файла")
                        continue
                    
                    existing_accounts = accounts_data.get("accounts", [])
                    imported_count = 0
                    
                    for acc in import_data['accounts']:
                        # Проверяем, нет ли уже такого аккаунта
                        existing = False
                        for existing_acc in existing_accounts:
                            if existing_acc.get('phone_number') == acc.get('phone_number'):
                                existing = True
                                break
                        
                        if not existing:
                            existing_accounts.append(acc)
                            imported_count += 1
                    
                    accounts_data["accounts"] = existing_accounts
                    await self.save_accounts(accounts_data)
                    
                    self.print_success(f"Импортировано аккаунтов: {imported_count}")
                    self.print_info(f"Всего аккаунтов теперь: {len(existing_accounts)}")
                    
                except Exception as e:
                    self.print_error(f"Ошибка импорта: {e}")
                    
            elif choice == '6':
                break
                
            else:
                self.print_error("Неверный выбор")
    
    async def main_menu(self):
        """Главное меню приложения"""
        while self.is_running:
            self.print_header("ГЛАВНОЕ МЕНЮ")
            
            if self.current_account:
                print(f"\033[1;32m👤 Текущий аккаунт: {self.current_account['name']}\033[0m")
                if self.current_account.get('proxy_url'):
                    print(f"\033[1;34m🔗 Прокси: используется\033[0m")
            else:
                print(f"\033[1;33m⚠ Аккаунт не выбран\033[0m")
            
            print("\n" + "═" * 60)
            self.print_menu_item("1", "Выбрать/добавить аккаунт", "👤")
            self.print_menu_item("2", "Статистика аккаунта", "📊")
            self.print_menu_item("3", "Рассылка сообщений", "📨")
            self.print_menu_item("4", "Проверить спам-блок", "🚫")
            self.print_menu_item("5", "Авто-подписка", "🤖")
            self.print_menu_item("6", "Автоответчик", "💬")
            self.print_menu_item("7", "Простые функции", "🔧")
            self.print_menu_item("8", "Управление аккаунтами", "⚙️")
            self.print_menu_item("9", "Сменить аккаунт", "🔄")
            self.print_menu_item("0", "Выход", "❌")
            print("═" * 60)
            
            choice = input("\n\033[1;37mВыберите действие: \033[0m").strip()
            
            if choice == '1':
                if not self.current_account:
                    account = await self.select_account()
                    if account:
                        await self.login_to_account(account)
                else:
                    self.print_info("Аккаунт уже выбран. Используйте пункт 'Сменить аккаунт'")
                    
            elif choice == '2':
                if not self.client:
                    self.print_error("Сначала выберите аккаунт")
                else:
                    await self.show_account_stats()
                    input("\n\033[1;37mНажмите Enter для продолжения...\033[0m")
                
            elif choice == '3':
                if not self.client:
                    self.print_error("Сначала выберите аккаунт")
                else:
                    # Инициализация переменных рассылки
                    self.mailing_message = ""
                    self.mailing_count = 1
                    self.mailing_delay = 10
                    
                    await self.mailing_menu()
                
            elif choice == '4':
                if not self.client:
                    self.print_error("Сначала выберите аккаунт")
                else:
                    await self.check_spam_block()
                    input("\n\033[1;37mНажмите Enter для продолжения...\033[0m")
                
            elif choice == '5':
                if not self.client:
                    self.print_error("Сначала выберите аккаунт")
                else:
                    if self.auto_subscribe_running:
                        self.print_warning("Авто-подписка уже запущена")
                    else:
                        await self.start_auto_subscribe()
                
            elif choice == '6':
                if not self.client:
                    self.print_error("Сначала выберите аккаунт")
                else:
                    await self.manage_auto_reply()
                
            elif choice == '7':
                if not self.client:
                    self.print_error("Сначала выберите аккаунт")
                else:
                    await self.simple_functions_menu()
                
            elif choice == '8':
                await self.manage_accounts()
                
            elif choice == '9':
                if self.client:
                    await self.client.stop()
                    self.client = None
                    self.current_account = None
                    self.print_success("Аккаунт отключен")
                
                account = await self.select_account()
                if account:
                    await self.login_to_account(account)
                
            elif choice == '0':
                print("\n\033[1;33mВыход из Monkey Gram...\033[0m")
                self.is_running = False
                self.auto_reply_running = False
                self.auto_subscribe_running = False
                self.stop_event.set()
                
                if self.client:
                    try:
                        await self.client.stop()
                    except:
                        pass
                break
                
            else:
                self.print_error("Неверный выбор")
    
    async def main(self):
        """Основная функция приложения"""
        # Очищаем экран
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Выводим логотип и обезьянку
        self.print_logo()
        self.print_monkey()
        
        print("\n\033[1;36m" + "═" * 60 + "\033[0m")
        print("\033[1;33m🐵 Добро пожаловать в Monkey Gram v2.0!\033[0m")
        print("\033[1;37mМощный менеджер Telegram аккаунтов\033[0m")
        print("\033[1;36m" + "═" * 60 + "\033[0m")
        
        # Проверка зависимостей
        self.print_info("Проверка зависимостей...")
        self.print_info("Если возникнут ошибки, установите вручную:")
        self.print_info("pip install pyrogram tgcrypto aiohttp")
        
        try:
            # Проверяем наличие сохраненных аккаунтов
            accounts_data = await self.load_accounts()
            accounts = accounts_data.get("accounts", [])
            
            if accounts:
                print(f"\n\033[1;32m✅ Найдено сохраненных аккаунтов: {len(accounts)}\033[0m")
                auto_login = input("\n\033[1;37mАвтоматически войти в последний аккаунт? (Y/n): \033[0m").strip().lower()
                
                if auto_login != 'n':
                    # Пробуем войти в последний использованный аккаунт
                    last_account = max(accounts, key=lambda x: x.get('last_login', ''), default=None)
                    if last_account:
                        self.print_info(f"Пробуем войти в аккаунт: {last_account['name']}")
                        if await self.login_to_account(last_account):
                            self.print_success("Автоматический вход выполнен!")
                        else:
                            self.print_warning("Автоматический вход не удался, выберите аккаунт вручную")
                            account = await self.select_account()
                            if account:
                                await self.login_to_account(account)
                    else:
                        account = await self.select_account()
                        if account:
                            await self.login_to_account(account)
                else:
                    account = await self.select_account()
                    if account:
                        await self.login_to_account(account)
            else:
                self.print_warning("Сохраненных аккаунтов нет")
                add_account = input("\n\033[1;37mДобавить новый аккаунт? (Y/n): \033[0m").strip().lower()
                if add_account != 'n':
                    await self.create_account()
                    # После создания пробуем войти
                    account = await self.select_account()
                    if account:
                        await self.login_to_account(account)
            
            # Запускаем главное меню
            await self.main_menu()
                
        except KeyboardInterrupt:
            self.print_warning("\n\nПриложение остановлено пользователем")
        except Exception as e:
            self.print_error(f"\nКритическая ошибка: {e}")
        finally:
            if self.client:
                try:
                    await self.client.stop()
                except:
                    pass
            
            print("\n\033[1;33m" + "═" * 60 + "\033[0m")
            print("\033[1;32m🐒 Спасибо за использование Monkey Gram!\033[0m")
            print("\033[1;33m" + "═" * 60 + "\033[0m")


if __name__ == "__main__":
    # Запуск приложения
    app = MonkeyGram()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        print("\n\n\033[1;33m⚠ Получен сигнал завершения...\033[0m")
        app.is_running = False
        app.auto_reply_running = False
        app.auto_subscribe_running = False
        app.stop_event.set()
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(app.main())
    except KeyboardInterrupt:
        print("\n\033[1;33mПриложение завершено\033[0m")
    except Exception as e:
        print(f"\n\033[1;31m✗ Фатальная ошибка: {e}\033[0m")
