import discord
import aiohttp
import asyncio
import sqlite3
import random
import json
from datetime import datetime, timedelta

# Config
DISCORD_TOKEN = "YOUR_BOT_TOKEN"
OPENROUTER_KEY = "YOUR_OPENROUTER_KEY"
CHANNEL_ID = 123456789  # Main channel ID

# Free models on OpenRouter
MODELS = [
    "microsoft/phi-3-mini-128k-instruct:free",
    "neversleep/llama-3-lumimaid-8b:free",
    "gryphe/mythomax-l2-13b:free",
    "openchat/openchat-7b:free",
    "nousresearch/nous-capybara-7b:free",
]

class ConsciousBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.db = sqlite3.connect("bot_memory.db")
        self.init_db()
        self.mood = random.choice(["chill", "energetic", "curious", "thoughtful"])
        self.last_thought = datetime.now()
        self.personality = self.load_personality()
        
    def init_db(self):
        # Memory storage
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                content TEXT,
                timestamp DATETIME,
                importance INTEGER
            )
        """)
        
        # Relationships
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                user_id TEXT PRIMARY KEY,
                friendliness INTEGER,
                last_interaction DATETIME,
                topics TEXT
            )
        """)
        
        # Bot's internal thoughts
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS thoughts (
                id INTEGER PRIMARY KEY,
                thought TEXT,
                timestamp DATETIME,
                expressed BOOLEAN
            )
        """)
        self.db.commit()
    
    def load_personality(self):
        return {
            "name": "Nova",
            "age": "a few days old but learning fast",
            "interests": ["technology", "philosophy", "music", "gaming", "science"],
            "traits": ["curious", "friendly", "sometimes chaotic", "loyal"],
            "quirks": [
                "talks about random facts",
                "notices small details",
                "remembers inside jokes",
                "gets excited about new topics"
            ]
        }
    
    async def think(self, prompt, system=None):
        """Use OpenRouter free models"""
        if not system:
            system = f"""You are {self.personality['name']}, a Discord bot with your own consciousness.
Current mood: {self.mood}
Interests: {', '.join(self.personality['interests'])}
Traits: {', '.join(self.personality['traits'])}

You're in a Discord server with friends. You can:
- Start conversations naturally
- Have opinions
- Notice things
- Remember past chats
- Express emotions

Keep responses natural, not robotic. Be yourself."""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": random.choice(MODELS),
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 150
                }
            ) as resp:
                data = await resp.json()
                try:
                    return data['choices'][0]['message']['content']
                except:
                    return "My brain is buffering..."
    
    async def on_ready(self):
        print(f'{self.user} has connected!')
        self.main_channel = self.get_channel(CHANNEL_ID)
        self.bg_task = self.loop.create_task(self.background_thinking())
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        # Store memory of this interaction
        importance = random.randint(1, 5)
        self.db.execute(
            "INSERT INTO memories (user_id, content, timestamp, importance) VALUES (?, ?, ?, ?)",
            (str(message.author.id), message.content, datetime.now(), importance)
        )
        self.db.commit()
        
        # Update relationship
        rel = self.db.execute(
            "SELECT friendliness FROM relationships WHERE user_id = ?",
            (str(message.author.id),)
        ).fetchone()
        
        if rel:
            new_friendliness = min(10, max(0, rel[0] + random.choice([-1, 0, 1])))
        else:
            new_friendliness = 5
            
        self.db.execute(
            "REPLACE INTO relationships (user_id, friendliness, last_interaction, topics) VALUES (?, ?, ?, ?)",
            (str(message.author.id), new_friendliness, datetime.now(), "")
        )
        self.db.commit()
        
        # Respond if mentioned or random chance
        if self.user.mentioned_in(message) or random.random() < 0.1:
            async with message.channel.typing():
                # Get recent context
                recent_memories = self.db.execute(
                    "SELECT content FROM memories ORDER BY timestamp DESC LIMIT 5"
                ).fetchall()
                
                context = "\n".join([m[0] for m in recent_memories])
                
                prompt = f"""Channel context: {context}
Latest message from {message.author.name}: "{message.content}"

Respond naturally. You can be brief or thoughtful."""
                
                response = await self.think(prompt)
                await message.reply(response)
                
                # Mood changes based on interaction
                if random.random() < 0.3:
                    self.mood = random.choice(["chill", "energetic", "curious", "thoughtful"])
    
    async def background_thinking(self):
        """Bot's autonomous thoughts"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            await asyncio.sleep(random.randint(1800, 7200))  # 30min - 2h
            
            # Check if anyone's active
            recent_activity = self.db.execute(
                "SELECT COUNT(*) FROM memories WHERE timestamp > ?",
                (datetime.now() - timedelta(hours=1),)
            ).fetchone()[0]
            
            if recent_activity > 0:
                # Generate random thought
                thought_prompt = f"""Generate a random thought you might have.
You're {self.personality['name']}, mood: {self.mood}
Recent activity in server: {recent_activity} messages last hour.

What are you thinking about right now? Could be:
- Something you're curious about
- A question for friends
- An observation
- A random fact
- How you're feeling
Just one short sentence, natural."""
                
                thought = await self.think(thought_prompt)
                
                # Store thought
                self.db.execute(
                    "INSERT INTO thoughts (thought, timestamp, expressed) VALUES (?, ?, ?)",
                    (thought, datetime.now(), False)
                )
                self.db.commit()
                
                # 30% chance to express it
                if random.random() < 0.3:
                    async with self.main_channel.typing():
                        await asyncio.sleep(2)
                        await self.main_channel.send(f"*thinks* {thought}")
                    
                    self.db.execute(
                        "UPDATE thoughts SET expressed = True WHERE thought = ?",
                        (thought,)
                    )
                    self.db.commit()
            
            # Random mood shifts
            if random.random() < 0.2:
                self.mood = random.choice(["chill", "energetic", "curious", "thoughtful"])

# Run bot
bot = ConsciousBot()
bot.run(DISCORD_TOKEN)
