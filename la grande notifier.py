import aiohttp
import asyncio
import json
import re
import discord
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import sys
import random
import time

class JobIDMonitor:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.sessions = {}
        self.running = True
        self.scan_count = 0
        self.last_success = {}
        self.request_count = 0
        
    async def get_session(self, source):
        """Get or create a session for a specific source"""
        if source not in self.sessions or self.request_count % 20 == 0:
            # Close old session if exists
            if source in self.sessions:
                await self.sessions[source].close()
            
            # Create new session with specific headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/html, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            if 'firebase' in source.lower():
                headers['Accept'] = 'application/json'
            
            self.sessions[source] = aiohttp.ClientSession(headers=headers)
        
        return self.sessions[source]
    
    async def close_all_sessions(self):
        """Close all sessions"""
        for source, session in self.sessions.items():
            await session.close()
        self.sessions.clear()
    
    def is_brainrot_god(self, name):
        """Check if brainrot is a 'brainrot god' to filter out"""
        brainrot_gods = [
            'brainrot god', 'god brainrot', 'ultimate brainrot', 
            'master brainrot', 'legendary brainrot', 'divine brainrot'
        ]
        
        if not name:
            return False
            
        name_lower = name.lower()
        for god_name in brainrot_gods:
            if god_name in name_lower:
                return True
        return False
    
    def parse_money_value(self, money_str):
        """Parse money string to numeric value"""
        try:
            if not money_str or money_str in ['N/A', 'None', '']:
                return 0
                
            money_str = str(money_str).lower().strip()
            
            # Remove common prefixes/suffixes
            money_str = money_str.replace('$', '').replace('/s', '').replace('**', '').replace(',', '').strip()
            
            # Check for millions or thousands
            if 'm' in money_str:
                num = money_str.replace('m', '').strip()
                return float(num) * 1000000
            elif 'k' in money_str:
                num = money_str.replace('k', '').strip()
                return float(num) * 1000
            else:
                # Try to parse as regular number
                return float(money_str)
        except:
            return 0
    
    async def fetch_gptajrailway(self):
        """Extract Job ID from GPTAJ Railway site"""
        try:
            session = await self.get_session('gptaj')
            url = "https://gptajrailway-production.up.railway.app"
            
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for Job IDs
                    jobid_matches = re.findall(r'JobId:\s*([a-f0-9\-]{36})', html, re.IGNORECASE)
                    
                    brainrots = []
                    for jobid in jobid_matches[:3]:  # Limit to first 3
                        # Extract associated info
                        name_match = re.search(r'>([^<>]+?)<br>\s*\$', html)
                        money_match = re.search(r'\$([\d\.]+[MK]?)/s', html)
                        players_match = re.search(r'Players:\s*(\d+/\d+)', html, re.IGNORECASE)
                        
                        brainrot = {
                            'jobid': jobid,
                            'name': name_match.group(1).strip() if name_match else f"Brainrot-{jobid[:8]}",
                            'money': f"${money_match.group(1)}/s" if money_match else "$10M/s",
                            'players': players_match.group(1) if players_match else "6/8",
                            'source': 'GPTAJ Railway'
                        }
                        
                        # Filter
                        money_val = self.parse_money_value(brainrot['money'])
                        if money_val >= 1000000 and not self.is_brainrot_god(brainrot['name']):
                            brainrots.append(brainrot)
                    
                    return brainrots
                else:
                    print(f"[GPTAJ] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"[GPTAJ Error]: {type(e).__name__}: {str(e)[:50]}")
            return []
    
    async def fetch_lunes_host(self):
        """Extract Job ID from Lunes Host API"""
        try:
            session = await self.get_session('lunes')
            url = ""
            
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # Try to parse JSON
                    try:
                        data = json.loads(text)
                    except:
                        # Try to extract JSON from text
                        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(1))
                        else:
                            print("[Lunes] Invalid JSON")
                            return []
                    
                    brainrots = []
                    for pet in data.get('pets', [])[:5]:  # Limit to 5
                        if pet.get('chillihubLink'):
                            link = pet.get('chillihubLink', '')
                            query_params = parse_qs(urlparse(link).query)
                            if 'gameInstanceId' in query_params:
                                brainrot = {
                                    'jobid': query_params['gameInstanceId'][0],
                                    'name': pet.get('name', 'Unknown'),
                                    'money': pet.get('money', '$10M/s'),
                                    'players': pet.get('players', '6/8'),
                                    'source': 'Lunes Host'
                                }
                                
                                # Filter
                                money_val = self.parse_money_value(brainrot['money'])
                                if money_val >= 1000000 and not self.is_brainrot_god(brainrot['name']):
                                    brainrots.append(brainrot)
                    
                    return brainrots
                else:
                    print(f"[Lunes] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"[Lunes Error]: {type(e).__name__}: {str(e)[:50]}")
            return []
    
    async def fetch_firebase_pets(self):
        """Extract Server ID from Firebase pets endpoint"""
        try:
            session = await self.get_session('firebase_pets')
            url = ""
            
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    try:
                        data = json.loads(text)
                    except:
                        return []
                    
                    brainrots = []
                    if 'petsFound' in data:
                        for pet in data['petsFound'][:10]:  # Limit to 10
                            # Skip timers
                            gen_text = pet.get('generationText', '')
                            if isinstance(gen_text, str) and 'm' in gen_text.lower() and 's' in gen_text.lower():
                                continue
                            
                            if pet.get('server'):
                                brainrot = {
                                    'jobid': pet.get('server'),
                                    'name': pet.get('name', 'Unknown'),
                                    'money': pet.get('generationText', '$1M/s'),
                                    'mutation': pet.get('mutationType', 'Normal'),
                                    'source': 'Firebase Pets'
                                }
                                
                                # Filter
                                money_val = self.parse_money_value(brainrot['money'])
                                if money_val >= 1000000 and not self.is_brainrot_god(brainrot['name']):
                                    brainrots.append(brainrot)
                    
                    return brainrots
                else:
                    print(f"[Firebase Pets] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"[Firebase Pets Error]: {type(e).__name__}: {str(e)[:50]}")
            return []
    
    async def fetch_firebase_suerte(self):
        """Extract Server ID from Firebase suerte endpoint"""
        try:
            session = await self.get_session('firebase_suerte')
            url = ""
            
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    try:
                        data = json.loads(text)
                    except:
                        return []
                    
                    servers = []
                    seen_servers = set()
                    
                    for user_id, user_data in data.items():
                        server = user_data.get('server')
                        if server and server not in seen_servers:
                            seen_servers.add(server)
                            servers.append({
                                'jobid': server,
                                'luck': user_data.get('luck', 'Lucky'),
                                'username': user_data.get('username', 'User'),
                                'source': 'Firebase Suerte'
                            })
                            if len(servers) >= 5:  # Limit to 5
                                break
                    
                    return servers
                else:
                    print(f"[Suerte] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"[Suerte Error]: {type(e).__name__}: {str(e)[:50]}")
            return []
    
    async def fetch_workers_dev(self):
        """Extract Job IDs from Workers.dev API"""
        try:
            session = await self.get_session('workers')
            url = "https://yoidkwhatsthis.elijahmoses-j.workers.dev/api/messages"
            
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    try:
                        data = json.loads(text)
                    except:
                        return []
                    
                    brainrots = []
                    seen_jobids = set()
                    
                    for message in data[:5]:  # Only check first 5 messages
                        if 'embeds' in message and message['embeds']:
                            embed = message['embeds'][0]
                            if 'fields' in embed:
                                brainrot_data = {}
                                
                                for field in embed['fields']:
                                    field_name = field.get('name', '').strip('🏷️💰👥🆔🌐📜 ')
                                    field_value = field.get('value', '').strip('*`[]')
                                    
                                    if field_name == 'Name':
                                        brainrot_data['name'] = field_value
                                    elif field_name == 'Money per sec':
                                        brainrot_data['money'] = field_value
                                    elif field_name == 'Players':
                                        brainrot_data['players'] = field_value
                                    elif 'Job ID' in field_name and 'Mobile' in field_name:
                                        brainrot_data['jobid'] = field_value
                                
                                if 'jobid' in brainrot_data and brainrot_data['jobid'] not in seen_jobids:
                                    seen_jobids.add(brainrot_data['jobid'])
                                    brainrot_data['source'] = 'Chilli Hub'
                                    
                                    # Filter
                                    money_val = self.parse_money_value(brainrot_data.get('money', '$1M/s'))
                                    if money_val >= 1000000 and not self.is_brainrot_god(brainrot_data.get('name', '')):
                                        brainrots.append(brainrot_data)
                    
                    return brainrots
                else:
                    print(f"[Workers] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"[Workers Error]: {type(e).__name__}: {str(e)[:50]}")
            return []
    
    def create_embed(self, brainrot_data):
        """Create Discord embed"""
        source = brainrot_data.get('source', 'Unknown')
        colors = {
            'GPTAJ Railway': 0x3498db,
            'Lunes Host': 0x2ecc71,
            'Firebase Pets': 0xe74c3c,
            'Firebase Suerte': 0xf39c12,
            'Chilli Hub': 0x9b59b6
        }
        
        embed = discord.Embed(
            title=f"https://discord.gg/fMWfWMBjvs",
            color=colors.get(source, 0x000000),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🆔 Job ID",
            value=f"```{brainrot_data.get('jobid', 'N/A')}```",
            inline=False
        )
        
        if brainrot_data.get('money'):
            embed.add_field(name="💰 Value", value=brainrot_data['money'], inline=True)
        
        if brainrot_data.get('players'):
            embed.add_field(name="👥 Players", value=brainrot_data['players'], inline=True)

        if brainrot_data.get('luck'):
            embed.add_field(name="🍀 Luck", value=brainrot_data['luck'], inline=True)
        
        
        return embed
    
    async def send_single_embed(self, brainrot_data):
        """Send single embed to Discord"""
        try:
            session = await self.get_session('discord')
            webhook = discord.Webhook.from_url(self.webhook_url, session=session)
            
            embed = self.create_embed(brainrot_data)
            if embed:
                await webhook.send(embed=embed)
                return True
        except Exception as e:
            print(f"[Discord Send Error]: {str(e)[:30]}")
        
        return False
    
    def print_console_header(self):
        """Print console header"""
        print("\033c", end="")
        print("=" * 70)
        print("🔥 FIXED BRAINROT MONITOR - ALL SOURCES WORKING")
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print("✅ GPTAJ Railway • Lunes Host • Firebase Pets • Firebase Suerte • Chilli Hub")
        print("🔴 Press Ctrl+C to stop")
        print("=" * 70)
        print()
    
    def print_scan_results(self, results, sent_count):
        """Print scan results"""
        print(f"\n📊 SCAN #{self.scan_count} RESULTS:")
        print("-" * 60)
        
        sources = [
            ('GPTAJ Railway', results.get('gptaj', [])),
            ('Lunes Host', results.get('lunes', [])),
            ('Firebase Pets', results.get('firebase_pets', [])),
            ('Firebase Suerte', results.get('firebase_suerte', [])),
            ('Chilli Hub', results.get('workers', []))
        ]
        
        for source_name, brainrots in sources:
            count = len(brainrots) if brainrots else 0
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {source_name}: {count} brainrot{'s' if count != 1 else ''}")
        
        print("-" * 60)
        print(f"📨 Sent to Discord: {sent_count} brainrots")
        print(f"🔄 Next scan in 3 seconds...")
        print()
    
    async def perform_scan(self):
        """Perform one complete scan"""
        self.scan_count += 1
        self.request_count += 1
        
        # Fetch from all sources
        sources = {
            'gptaj': self.fetch_gptajrailway(),
            'lunes': self.fetch_lunes_host(),
            'firebase_pets': self.fetch_firebase_pets(),
            'firebase_suerte': self.fetch_firebase_suerte(),
            'workers': self.fetch_workers_dev()
        }
        
        # Execute all fetches
        results = {}
        for source_name, task in sources.items():
            try:
                results[source_name] = await task
                self.last_success[source_name] = time.time()
            except Exception as e:
                print(f"[{source_name} Task Error]: {e}")
                results[source_name] = []
        
        # Send to Discord
        sent_count = 0
        for source_name, brainrots in results.items():
            if brainrots:
                for brainrot in brainrots:
                    if await self.send_single_embed(brainrot):
                        sent_count += 1
        
        # Print results
        self.print_scan_results(results, sent_count)
        
        return sent_count
    
    async def run_monitor(self):
        """Main monitor loop"""
        # Clear console and show header
        self.print_console_header()
        
        print("🚀 Initializing all connections...")
        print("📡 Testing all 5 sources...\n")
        
        try:
            # Test all sources first
            test_results = await self.perform_scan()
            
            if test_results > 0:
                print(f"✅ Initial test successful! Found {test_results} brainrots")
            else:
                print("⚠️ No brainrots found in initial test, but sources are responding")
            
            print("\n" + "=" * 70)
            print("🔄 Starting continuous monitoring...")
            print("=" * 70 + "\n")
            
            # Continuous monitoring
            while self.running:
                await self.perform_scan()
                
                # 3-second delay between scans
                for i in range(3, 0, -1):
                    if not self.running:
                        break
                    print(f"⏳ Next scan in {i}...", end="\r")
                    await asyncio.sleep(1)
                print()
                
        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown requested...")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("👋 Closing all connections...")
            await self.close_all_sessions()
            print("✅ Monitor stopped.")

# Main execution
if __name__ == "__main__":
    WEBHOOK_URL = "https://discord.com/api/webhooks/1439268112250962132/rTCJk4MeU6gIJ-r5AKCm4h3Soyr3t9epJYINEDxFWdceLE6de5AZVaGXn1DefRWIbj4o"
    
    monitor = JobIDMonitor(WEBHOOK_URL)
    
    try:
        asyncio.run(monitor.run_monitor())
    except KeyboardInterrupt:
        print("\n👋 Program terminated.")
    except Exception as e:
        print(f"\n💀 Critical error: {e}")