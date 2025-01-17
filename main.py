import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

FFMPEG_OPTIONS = {
    'options':'-vn',
    'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}
YDL_OPTIONS = {
'format': 'bestaudio', 'noplaylist': True
}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.loop = False
        self.current_song = None

    @commands.hybrid_command(name="play", description="Spielt ein Lied ab")
    async def play(self, ctx: commands.Context, * , search: str):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
          return await ctx.send("Du bist nicht in einem Sprachkanal")
    
        if not ctx.voice_client:
         await voice_channel.connect()


        async with ctx.typing():
         with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{search}", download = False)
            except Exception as e:
                return await ctx.send(f"Fehler beim Abrufen von Informationen: {str(e)}")
            
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title  = info['title']
            self.queue.append((url, title))
            await ctx.send(f"Zur queue hinzugefügt: **{title}**")

        if not ctx.voice_client.is_playing():
         await self.play_next(ctx)

    async def play_next(self, ctx:commands.Context):
        if self.loop and self.current_song:
          url, title = self.current_song
        elif self.queue:
          url, title = self.queue.pop(0)
          self.current_song = (url, title)
        else:
          self.current_song = None
          return await ctx.send("Queue ist leer!")
       
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=lambda e: self.client.loop.create_task(self.play_next(ctx)))
        await ctx.send(f"Gerade läuft: **{title}**")
    @commands.hybrid_command(name="skip", description="Überspringt das aktuelle lied")
    async def skip(self, ctx: commands.Context):
       if ctx.voice_client and ctx.voice_client.is_playing():
          ctx.voice_client.stop()
          await ctx.send("Lied übersprungen!")


    @commands.hybrid_command(name="pause", description="Pausiert das AKutelle Lied")
    async def pause(self, ctx: commands.Context):
       if ctx.voice_client:
          if ctx.voice_client.is_paused():
             await ctx.send("Wiedergabe ist bereits pausiert!", ephemeral=True)

          elif ctx.voice_client.is_playing():
             ctx.voice_client.pause()
             await ctx.send("Wiedergabe Pausiert")
          else:
              await ctx.send("Es wird gerade nichts abgespielt", ephemeral=True)


    @commands.hybrid_command(name="resume", description="Setzt das aktuelle Lied fort")
    async def resume(self, ctx:commands.Context):
       if ctx.voice_client:
          if ctx.voice_client.is_paused():
             ctx.voice_client.resume()
             await ctx.send("Wiedergabe fortgesetzt")
          elif ctx.voice_client.is_playing():
              await ctx.send("Die Wiedergabe läuft bereits!", ephemeral=True)
          else:
             await ctx.send("Es wird gerade nichts abgespielt", ephemeral=True)

    @commands.hybrid_command(name="loop", description="Schaltet den Loop modus ein/aus")
    async def loop(self, ctx: commands.Context):
      self.loop = not self.loop
      if self.loop:
         await ctx.send("Loop Modus Aktiviert")
      else:
         await ctx.send("Loop Modus deaktiviert!")


client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
   await client.tree.sync()
   print("Bot ist Bereit")
async def main():
   await client.add_cog(MusicBot(client))
   await client.start('DEIN BOT TOKEN HIER')

asyncio.run(main())