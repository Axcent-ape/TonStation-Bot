import json
import random
from utils.core import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
import asyncio
from urllib.parse import unquote, quote
from data import config
import aiohttp
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector
from datetime import datetime
import time


class TonStation:
    def __init__(self, thread: int, session_name: str, phone_number: str, proxy: [str, None]):
        self.account = session_name + '.session'
        self.thread = thread

        self.user_id, self.user_info = None, None
        self.sp = 'ref_buzjtu7gvm6eyna393psdl'
        self.proxy = f"{config.PROXY['TYPE']['REQUESTS']}://{proxy}" if proxy is not None else None
        connector = ProxyConnector.from_url(self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)

        if proxy:
            proxy = {
                "scheme": config.PROXY['TYPE']['TG'],
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }

        self.client = Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            workdir=config.WORKDIR,
            proxy=proxy,
            lang_code='ru'
        )

        headers = {'User-Agent': UserAgent(os='android').random}
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def stats(self):
        await self.login()

        farming = await self.farming_running()
        balance = 0 if farming.get('amount') is None else farming.get('amount')

        r = await (await self.session.get(f'https://tonstation.app/referral/api/v1/referrals/{self.user_id}/available-number')).json()
        referrals = r.get('data').get('referralCount')

        await self.logout()

        await self.client.connect()
        me = await self.client.get_me()
        phone_number, name = "'" + me.phone_number, f"{me.first_name} {me.last_name if me.last_name is not None else ''}"
        await self.client.disconnect()

        proxy = self.proxy.replace('http://', "") if self.proxy is not None else '-'

        return [phone_number, name, str(balance), str(referrals), proxy]

    async def get_tasks(self):
        resp = await self.session.get(f'https://tonstation.app/quests/api/v1/quests?userId={self.user_id}&size=50')
        # print('get_tasks', await resp.text())
        return (await resp.json()).get('data')

    async def task_start(self, project: str, quest_id: str):
        json_data = {
          "project": project,
          "userId": self.user_id,
          "questId": quest_id
        }

        resp = await self.session.post(f'https://tonstation.app/quests/api/v1/start', json=json_data)
        return (await resp.json()).get('data')[0] if resp.status == 200 else False

    async def farming_claim(self, task_id: str):
        json_data = {
            "userId": self.user_id,
            "taskId": task_id
        }

        resp = await self.session.post(f'https://tonstation.app/farming/api/v1/farming/claim', json=json_data)
        # print('farming_claim', await resp.text())
        return (await resp.json()).get('data')

    async def farming_running(self):
        resp = await self.session.get(f'https://tonstation.app/farming/api/v1/farming/{self.user_id}/running')
        # print('farming_running', await resp.text())
        r = await resp.json()
        return r.get('data')[0] if resp.status == 200 and r.get('data') else False

    async def farming_start(self):
        json_data = {"userId": self.user_id, "taskId": "1"}
        resp = await self.session.post(f'https://tonstation.app/farming/api/v1/farming/start', json=json_data)
        # print('farming_start', await resp.text())
        return resp.status == 200

    async def balance_by_address(self):
        resp = await self.session.get(f'https://tonstation.app/balance/api/v1/balance/{self.user_info["address"]}/by-address')
        return (await resp.json()).get('data')

    async def get_user_profile(self):
        resp = await self.session.get(f'https://tonstation.app/userprofile/api/v1/users/{self.user_id}/by-telegram-id')
        return await resp.json()

    async def logout(self):
        await self.session.close()

    async def login(self):
        attempts = 3
        while attempts:
            try:
                self.sp = 'ref_c5xdxw4chx7duptkojrjq5'
                await asyncio.sleep(random.uniform(*config.DELAYS['ACCOUNT']))
                query = await self.get_tg_web_data()

                if query is None:
                    logger.error(f"Thread {self.thread} | {self.account} | Session {self.account} invalid")
                    await self.logout()
                    return None

                ans = await self.get_user_profile()
                if ans.get('code') == 404:
                    url = 'https://tonstation.app/userprofile/api/v1/users'
                else:
                    url = 'https://tonstation.app/userprofile/api/v1/users/auth'
                    self.user_info = ans

                r = await (await self.session.post(url, json={"initData": query})).json()

                if r.get('user'):
                    logger.success(f"Thread {self.thread} | {self.account} | Registered!")
                    self.user_info = r.get('user')

                access_token = r.get('session').get('accessToken') if r.get('user') else r.get('accessToken')

                self.session.headers['Authorization'] = 'Bearer ' + access_token
                logger.success(f"Thread {self.thread} | {self.account} | Login")
                break
            except Exception as e:
                logger.error(f"Thread {self.thread} | {self.account} | Left login attempts: {attempts}, error: {e}")
                await asyncio.sleep(random.uniform(*config.DELAYS['RELOGIN']))
                attempts -= 1
        else:
            logger.error(f"Thread {self.thread} | {self.account} | Couldn't login")
            await self.logout()
            return

    async def get_tg_web_data(self):
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestAppWebView(
                peer=await self.client.resolve_peer('tonstationgames_bot'),
                app=InputBotAppShortName(bot_id=await self.client.resolve_peer('tonstationgames_bot'), short_name="app"),
                platform='android',
                write_allowed=True,
                start_param=self.sp
            ))
            await self.client.disconnect()
            auth_url = web_view.url

            query = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            user = unquote(query.split("user=")[1].split('&chat_instance')[0])
            self.user_id = str(json.loads(unquote(user))['id'])

            return query
        except:
            return None

    @staticmethod
    def iso_to_unix_time(iso_time: str):
        return int(datetime.fromisoformat(iso_time.replace("Z", "+00:00")).timestamp()) + 1

    @staticmethod
    def current_time():
        return int(time.time())
