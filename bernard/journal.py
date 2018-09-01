import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.database as database
import logging
import asyncio
import time
from datetime import datetime
logger = logging.getLogger(__name__)
logger.info("loading...")

#handle auditing_blacklist_domains control
@discord.bot.command(pass_context=True, hidden=True)
async def journal(ctx, user: str):
    if common.isDiscordRegulator(ctx.message.author) is False:
        return

    try:
        member = ctx.message.mentions[0]
    except IndexError:
        member = ctx.message.server.get_member(user)
        if member is None:
            member = ctx.message.server.get_member_named(user)

    if member is None:
        database.cursor.execute('SELECT * from journal_events WHERE userid=%s ORDER BY time DESC LIMIT 5', (user,))
        emd = discord.embeds.Embed(title='Last 5 events for ({0})'.format(user), color=0xE79015)
    else:
        database.cursor.execute('SELECT * from journal_events WHERE userid=%s ORDER BY time DESC LIMIT 5', (member.id,))
        emd = discord.embeds.Embed(title='Last 5 events for "{0.name}" ({0.id})'.format(member), color=0xE79015)

    dbres = database.cursor.fetchall()

    if len(dbres) == 0:
        await discord.bot.say("Not found in my journal :(")
        return
    else:
        for row in dbres:
            emd.add_field(inline=False,name="{}".format(datetime.fromtimestamp(float(row['time'])).isoformat()), value="{0[event]}({0[module]}) Result: {0[contents]}\n".format(row))
        await discord.bot.say(embed=emd)

def update_journal_job(**kwargs):
    module = kwargs['module']
    job = kwargs['job']
    start = kwargs['start']
    result = kwargs['result']
    runtime = round(time.time() - start, 4)

    database.cursor.execute('INSERT INTO journal_jobs'
                            '(module, job, time, runtime, result)'
                            'VALUES (%s,%s,%s,%s,%s)',
                            (module, job, time.time(), runtime, result))
    database.connection.commit()

def update_journal_event(**kwargs):
    module = kwargs['module']
    event = kwargs['event']
    userid = kwargs['userid']
    try:
        eventid = kwargs['eventid']
    except KeyError:
        eventid = None
    contents = kwargs['contents']

    database.cursor.execute('INSERT INTO journal_events'
                            '(module, event, time, userid, eventid, contents)'
                            'VALUES (%s,%s,%s,%s,%s,%s)',
                            (module, event, time.time(), userid, eventid, contents))
    database.connection.commit()

def update_journal_regulator(**kwargs):
    invoker = kwargs['invoker']
    target = kwargs['target']
    eventdata = kwargs['eventdata']
    action = kwargs['action']
    try:
        message = kwargs['messageid']
    except KeyError:
        message = None

    database.cursor.execute('INSERT INTO journal_regulators'
                            '(id_invoker, id_targeted, id_message, action, time, event)'
                            'VALUES (%s,%s,%s,%s,%s,%s)',
                            (invoker, target, eventdata, action, time.time(), message))
    database.connection.commit()
