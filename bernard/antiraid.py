import bernard.scheduler as scheduler
import bernard.common as common
import bernard.config as config
import bernard.discord
import logging
import time

logger = logging.getLogger(__name__)
logger.info("loading...")


@bernard.discord.bot.command(pass_context=True, no_pm=True, hidden=True)
async def raidmode(ctx, operation="enable", duration="15m"):
    if common.isDiscordMainServer(ctx.message.server) is not True:
        return

    # Make sure only regulators can turn on raid mode
    if not common.isDiscordRegulator(ctx.message.author):
        return

    # if the user is looking for help, return the help information
    if operation.lower() == "help":
        await bernard.discord.bot.say(
            "⚠️{0.message.author.mention} help information for raid mode:"
            "This command will lock down voice and text channels to users with a verified role for the duration specified. **Use with extreme caution.**"
            "```"
            "!raidmode - enables raid mode with a default duration of 15 minutes"
            "!raidmode enable 10m - enables raid mode for 10 minutes"
            "!raidmode disable - disables raid mode```".format(
                ctx))
        return

    # If the operations isn't help, enable, or disable, kick a syntax error to the user
    if "enable" not in operation.lower() and "disable" not in operation.lower():
        await bernard.discord.bot.say(
            "⚠️{0.message.author.mention} invalid syntax. See !raidmode help` for information on using raid mode`".format(
                ctx))
        return

    if operation.lower() == "disable":
        await bernard.discord.bot.say("PLACEHOLDER - Disabling raid mode.")
        return

    # Get the duration in seconds from user input
    duration_length = scheduler.user_duration_to_seconds(duration)
    if duration_length is False:
        await bernard.discord.bot.say(
            "⚠️{0.message.author.mention} unable to decode message length. Correct format is `!raidmode enable 10m|60m|2h`".format(
                ctx))
        return
    elif duration_length is None:
        await bernard.discord.bot.say(
            "⚠️{0.message.author.mention} unable to decode message length. allowed: seconds (s), minutes (m), hours (h)".format(
                ctx))
        return

    # Ensure duration fits within configured boundaries
    if duration_length < config.cfg['antiraid']['time_range_min_mins'] or duration_length > int(config.cfg['antiraid']['time_range_max_mins'] * 60):
        await bernard.discord.bot.say("⚠️{0.message.author.mention} Anti-raid duration is out of expected range. "
                                      "Current Range {1}m to {2}h".format(ctx, config.cfg['scheduler']['time_range_min_mins'],
                                                                          int(config.cfg['scheduler']['time_range_max_mins'] / 60)))
        return

    # Enable raid mode
    msg = await bernard.discord.bot.send_message(ctx.message.channel, "**Enabling raid mode for {0}.** "
                                                                      "*Are you sure you want to do this?*".format(duration))
    await bernard.discord.bot.add_reaction(message=msg, emoji="✅")
    await bernard.discord.bot.add_reaction(message=msg, emoji="❌")
    reaction = await bernard.discord.bot.wait_for_reaction(user=ctx.message.author, message=msg, timeout=60.0, emoji=["✅", "❌"])

    if reaction.reaction.emoji == "✅":
        await bernard.discord.bot.say("PLACEHOLDER - Enabling raid mode.")
        return
    elif reaction.reaction.emoji == "❌":
        await bernard.discord.bot.say("PLACEHOLDER - Cancelling request.")
        return

    # Set some kind of variable to track that raid mode is enabled

    # Calculate when raid mode should be disabled
    now = int(time.time())
    time_to_fire = now + duration_length

    # set the reminder
    # scheduler.set_future_task(
    #     invoker=ctx.message.author.id,
    #     channel=ctx.message.channel.id,
    #     timestamp=time_to_fire,
    #     event="POST_MESSAGE",
    #     msg=text)

    await bernard.discord.bot.say(
        "✔️{0.message.author.mention} raid mode enabled for {1}! Disable early with `!raidmode disable`".format(
            ctx, duration))
