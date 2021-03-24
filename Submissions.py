# general notice, only put one class inside of a module, else shit might break

# every class gets the self.prefix variable on initiation, which just returns 

from discord.ext import commands # important, do not remove
from discord import File, Embed, Member, PermissionOverwrite
from utils import not_self, embed_message

class Submissions(commands.Cog):

    # Config

    admin_role = 802993317171429446
    submissions_channel = 802577372108423230
    archived_submissions_category = 804837609934815244 # category where archived submissions go
    approval_reaction = '✅' # what emoji should be used to approve submissions
    rejection_reaction = '<:white_x_mark:810490246277234718>'

    # Config End

    async def __asinit__(self):
        self.archived_submissions_category = await self.bot.fetch_channel(self.archived_submissions_category)
        self.admin_role = self.archived_submissions_category.guild.get_role(self.admin_role)

    def help_message(self):
        return """Manages submissions to the server.
 \> Any submissions posted in <#{0}> will be reviewed.""".format(self.submissions_channel) # CHANGE THIS TOO --- DONE --- NOT DONE, IT IS NEVER DONE 🔫
    @commands.Cog.listener()
    @not_self()
    async def on_raw_reaction_add(self, ctx):
        if ctx.channel_id == self.submissions_channel:
            channel = await self.bot.fetch_channel(ctx.channel_id)
            message = await channel.fetch_message(ctx.message_id)
            if channel.permissions_for(ctx.member).administrator:
                if str(ctx.emoji) == self.approval_reaction:
                    for archived_channel in self.archived_submissions_category.channels:
                        try:
                            if message.author.id == int(archived_channel.name.split('submission-discussion-')[1]):
                                await self.submission_reopen(message, archived_channel)
                                return await message.remove_reaction(ctx.emoji, ctx.member)
                        except IndexError:
                            pass
                        except ValueError:
                            pass
                    await self.submission_open(message)
                    await message.remove_reaction(ctx.emoji, ctx.member)
                elif str(ctx.emoji) == self.rejection_reaction:
                    await self.rejected(message.author)
                    await embed_message(message.author, message)
                    return await message.remove_reaction(ctx.emoji, ctx.member)

    async def submission_open(self, message):
        overwrites = {
            message.guild.default_role: PermissionOverwrite(read_messages=False),
            message.author: PermissionOverwrite(read_messages=True, send_messages=True),
            self.admin_role: PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True)
        }
        channel = await message.channel.category.create_text_channel(name='submission-discussion', overwrites=overwrites, topic="Send /close to end the discussion.")
        embed = Embed(title="This is the start of your discussion about your submission.", color=0x4F71C6)
        await channel.send(embed=embed)
        await embed_message(channel, message)
        await self.approved(message.author, channel)

    async def submission_reopen(self, message, channel):
        overwrites = {
            message.guild.default_role: PermissionOverwrite(read_messages=False),
            message.author: PermissionOverwrite(read_messages=True, send_messages=True),
            self.admin_role: PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True)
        }
        await channel.edit(name='submission-discussion', overwrites=overwrites, category=message.channel.category)
        embed = Embed(title="This is the start of your discussion about your submission.", color=0x4F71C6)
        await channel.send(embed=embed)
        await embed_message(channel, message)
        await self.approved(message.author, channel)

    async def approved(self, ctx, channel):
        file = File(open('images/approved.png', 'rb'), 'approved.png')
        embed = Embed(title="Your Submission has been approved!", description="Congratulations!", color=0x77B454)
        embed.set_thumbnail(url='attachment://approved.png')
        embed.set_footer(text='© ' + self.archived_submissions_category.guild.name, icon_url=self.archived_submissions_category.guild.icon_url)
        embed.add_field(name="What's next?", value="You can discuss it with an Admin here:\n<#{}>".format(channel.id))
        await ctx.send(file=file, embed=embed)

    async def rejected(self, ctx):
        file = File(open('images/rejected.png', 'rb'), 'rejected.png')
        embed = Embed(title="Sorry, but your submission has been rejected.", color=0xDC2D43)
        embed.set_thumbnail(url='attachment://rejected.png')
        embed.set_footer(text='© ' + self.archived_submissions_category.guild.name, icon_url=self.archived_submissions_category.guild.icon_url)
        await ctx.send(file=file, embed=embed)

    @commands.command()
    @not_self()
    async def close(self, ctx):
        try:
            if ctx.channel.name == 'submission-discussion':
                if ctx.channel.permissions_for(ctx.author).administrator:
                    overwrites = ctx.channel.overwrites
                    for key, value in overwrites.items():
                        if isinstance(key, Member):
                            author = key
                            break
                    overwrites = {
                        ctx.guild.default_role: PermissionOverwrite(read_messages=False),
                        author: PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=False),
                        self.admin_role: PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True)
                    }
                    embed = Embed(title="This discussion has been closed.", color=0x4F71C6)
                    await ctx.channel.send(embed=embed)
                    await ctx.channel.edit(name=ctx.channel.name + '-' + str(author.id), category=self.archived_submissions_category, overwrites=overwrites, sync_permissions=True)
        except Exception as e:
            print(e)