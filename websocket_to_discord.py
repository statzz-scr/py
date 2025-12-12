import asyncio
import websockets
import requests
import json

# 🔧 CONFIGURATION
WS_URL = "ws://144.172.110.44:1488"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1431384597962162342/GP6-6Y771cfS43Pd-nVoel3ubhyzAE6CDct3CkU_XIGPdN2WWx4C1MCya2XlDgLm7Mqz"

# 🧠 High-value brainrots that trigger @everyone
HIGH_VALUE_BRAINROTS = {
    "Dragon Cannelloni",
    "Burguro And Fryuro",
    "La Secret Combinasion",
    "Spooky and Pumpky",
    "Spaghetti Tualetti",
    "Garama and Madundung",
    "Ketchuru and Musturu",
    "La Supreme Combinasion"
}

async def forward_messages():
    async with websockets.connect(WS_URL) as ws:
        print(f"✅ Connected to {WS_URL}")
        while True:
            try:
                message = await ws.recv()
                print(f"📩 Received: {message}")

                # Parse JSON
                try:
                    data = json.loads(message)
                    brainrot = data.get("name", "Unknown Brainrot")
                    rate = data.get("money", "N/A")
                    jobid = data.get("jobid", "Unknown JobID")
                except Exception as e:
                    print(f"⚠️ JSON parse error: {e}")
                    brainrot, rate, jobid = message, "N/A", "Unknown"

                ping = brainrot in HIGH_VALUE_BRAINROTS

                embed = {
                    "username": "Brainrot Notify • 1M–9M",
                    "embeds": [
                        {
                            "title": f"Highest: {brainrot} | {rate}",
                            "color": 0x5C2E91,
                            "fields": [
                                {"name": "🧠 Brainrot", "value": f"**{brainrot}**", "inline": False},
                                {"name": "💸 Money", "value": f"**{rate}**", "inline": False},
                                {"name": "🆔 JobID", "value": f"```{jobid}```", "inline": False}
                            ],
                            "footer": {
                                "text": "tiktok: justalex208 • https://discord.gg/prMUWtBB6T"
                            }
                        }
                    ],
                    "content": "@everyone 💥 High-value brainrot detected!" if ping else ""
                }

                # Send to Discord webhook
                response = requests.post(DISCORD_WEBHOOK_URL, json=embed)
                if response.status_code not in (200, 204):
                    print(f"⚠️ Failed to send: {response.text}")
                else:
                    print(f"✅ Sent embed for {brainrot} ({'pinged @everyone' if ping else 'no ping'})")

            except websockets.ConnectionClosed:
                print("⚠️ WebSocket disconnected. Reconnecting in 5s...")
                await asyncio.sleep(5)
                return await forward_messages()
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(2)

# Run the bot
asyncio.run(forward_messages())
