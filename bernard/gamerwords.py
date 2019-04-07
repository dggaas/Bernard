import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.database as database
import datetime
import logging
import re
import time

logger = logging.getLogger(__name__)
logger.info("loading...")

def regex_scoring_msg(msg):
    # https://www.reddit.com/r/modhelp/comments/4g8lpo/would_you_be_willing_to_share_your_slur_filter_if/
    regex_mapping = {
        'testing_gamerword_filter_test': 500,
        'n1gga|n1gger|nigg3r|n1gg3r|nigga|niggah|niggas|niggaz|nigger|niggers': 200,
        'fag|fagging|faggitt|faggot|faggs|fagot|fagots|fags': 100,
        'k[iy]+kes?|goyim': 100,
        'tranny': 100,
        'retar(d|ded|ds)': 80,
        'autis[tm]?': 50,
        'kill\\s*your(self|selves)|kys': 20
    }

    msg_score = 0 # set the base score to 0
    for regex, weight in regex_mapping.items(): # loop through every regex case
        for word in msg.split(): # split the string up into words for multiplyers (someone spamming same slur over and over)
            for match in re.findall("\\b"+regex+"\\b", word, re.IGNORECASE): # search that word against the regex
                msg_score += weight # add up the score
                #print(msg, match, regex, weight)

    if msg_score is not 0:
        logger.info("regex_scoring_message(): WEIGHT: {}, MSG: {}".format(msg_score, msg))
    return msg_score

def member_age_scoring(age):
    # in minutes, format: age, multiplier
    multiplier_map = {
        60: 5, # 60m
        360: 4, # 6 hours
        1440: 3, # 1 day
        4320: 3.5, # 3 days
        10080: 2, # 1 week
        20160: 1.5, # 2 weeks
        40320: 1.15 # 1 month
    }

    for map_age, weight in multiplier_map.items():
        if age < map_age:
            logger.info("member_age_scoring(): MEMBER MULTIPLIER: {}".format(weight))
            return weight

    return 0

def account_age_scoring(age):
    # in minutes, format: age, multiplier
    multiplier_map = {
        60: 10, # 1 hour
        1440: 7.5, # 1 day
        10080: 5, # 1 week
        40320: 2.5, # 1 month
        120960: 1.5, # 3 months
    }

    for map_age, weight in multiplier_map.items():
        if age < map_age:
            print("account_age_scoring(): ACCOUNT MULTIPLIER: {}".format(weight))
            return weight

    return 0

async def slur_filter(message):
    # get the score of the message contents
    msg_score = regex_scoring_msg(message.content)

    # if the message scored 0, we can ignore
    if msg_score == 0:
        return

    # if we got this far, we need to lookup their account age
    account_min_old = int((datetime.datetime.utcnow().timestamp() - message.author.created_at.timestamp()) / 60)
    account_age_score = account_age_scoring(account_min_old)

    # and the amount of time in the discord
    database.cursor.execute('SELECT * from journal_events WHERE userid=%s AND event = \'ON_MEMBER_JOIN\' ORDER BY `time` DESC LIMIT 1', (message.author.id,))
    dbres = database.cursor.fetchone()
    if dbres is None:
        account_member_score = 0
    else:
        time_since_join = int((time.time() - dbres['time']) / 60)
        account_member_score = member_age_scoring(time_since_join)

    multiplier = account_age_score + account_member_score
    if multiplier is not 0:
        final_score = msg_score * multiplier
    else:
        final_score = msg_score

    # log the action to the database
    database.cursor.execute('INSERT INTO automod_gamerwords'
                            '(score_final, score_regex, multiply_age_member, multiply_age_account, time, id_targeted, message)'
                            'VALUES (%s,%s,%s,%s,%s,%s,%s)',
                            (final_score, msg_score, account_member_score, account_age_score, time.time(), message.author.id, message.content))
    database.connection.commit()
