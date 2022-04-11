'Generates a schedule of pairs of people to chat 1:1'

import argparse
import collections
import random
import json
import datetime
import time
from slack_sdk import WebClient
import os

import dateutil.parser
from dateutil.relativedelta import relativedelta

import urllib.request

DEBUG = False


def send_slack_message(config, text):
    if DEBUG:
        print(text)
        return

    if config.get('slack_webhook_url'):
        r = urllib.request.Request(config['slack_webhook_url'],
                                   data=json.dumps({'text': text}).encode('utf-8'),
                                   headers={
                                       'Content-Type': 'application/json'
                                   },
                                   method='POST')
        with urllib.request.urlopen(r):
            pass

    elif config.get('slack_bot_token'):
        client = WebClient(token=config['slack_bot_token'])
        client.chat_postMessage(channel=config['channel_id'], text=text)


def generate_pairs(names, seed, past_pairs, max_tries=50):
    for k in range(max_tries):
        pending = names.copy()
        random.shuffle(pending)

        pairs = []

        for i in range(len(names) // 2):
            p = pending[0]
            candidates = [n 
                          for n in pending
                          if (n != p and
                              (n, p) not in past_pairs and
                              (n, p) not in pairs and
                              (p, n) not in past_pairs and
                              (p, n) not in pairs)]

            if len(candidates) == 0:
                print('No candidates -- starting over...')
                break

            p2 = random.choice(candidates)
            pending.remove(p)
            pending.remove(p2)
            pairs.append((p, p2))

        if 2*len(pairs) == len(names):
            break

    return pairs


def parse_quotes_file(path):
    quotes = []
    current_quote = []

    with open(path) as f:
        for line in f:
            if line.strip() == '%':
                quotes.append(''.join(current_quote))
                current_quote = []
            else:
                current_quote.append(line)
    return quotes


def format_participant(p):
    return f'{p["name"]} (<@{p["id"]}>)'


def execute(config_path):
    with open(config_path) as f:
        config = json.load(f)

    names = config['names']
    rounds = config['rounds']
    seed = config['seed']

    # Ensure past_pairs exists.
    config['past_pairs'] = config.get('past_pairs', [])

    random.seed(seed)

    # slack_webhook_url = config['slack_webhook_url']
    start_date = dateutil.parser.parse(config['start_date']).date()
    frequency_weeks = relativedelta(weeks=config['frequency_weeks'])
    message_header = config['message_header']
    participants = config['participants']
    quotes_file = config.get('quotes_file')
    quotes = parse_quotes_file(quotes_file)

    # See if today is a day to send pairs:
    today = datetime.date.today()
    current = start_date
    n_round = 0

    while current < today:
        n_round += 1
        current += frequency_weeks

    if True:
        ids = [p['id'] for p in participants]
        p_by_id = {p['id']: p for p in participants}

        ps = generate_pairs(ids, seed, set((a, b) for [a, b] in config['past_pairs']))

        if ps:
            random_quote = quotes[int(time.time()) % len(quotes)]

            slack_message = "\n".join([
                message_header,
                *[f'{format_participant(p_by_id[a])} and {format_participant(p_by_id[b])}' for a, b in ps],
                '',
                'If you\'re really out of ideas, here\'s how you can start the conversation:',
                random_quote
            ])
            send_slack_message(config, slack_message)

            if not DEBUG:
                config['past_pairs'].extend(ps)
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                print('Updated', config_path)
        else:
            send_slack_message(config, "We're out of scheduled chats! Time to do this again?")

    elif quotes_file:
        send_slack_message(config,
                           'I have an important message to the group:\n\n' + random_quote)


def setup_from_reactions(config_path):
    with open(config_path) as f:
        config = json.load(f)

    client = WebClient(token=config.get('slack_bot_token') or os.environ['SLACK_BOT_TOKEN'])

    response = client.conversations_history(channel=config['channel_id'])
    messages = response['messages']

    print(len(messages), 'messages.')

    for m in messages:
        if 'text' in m and m['text'].startswith(config['kickstart_message_prefix']):
            reactions_response = client.reactions_get(full=True,
                                                      channel=config['channel_id'],
                                                      timestamp=m['ts'])

            participant_ids = set()

            for r in reactions_response.data['message']['reactions']:
                for u in r['users']:
                    participant_ids.add(u)

            participants = []

            print(len(participant_ids), 'participants:')
            for p_id in participant_ids:
                profile = client.users_profile_get(user=p_id).data['profile']
                name = profile.get('display_name') or profile.get('first_name') or profile.get('real_name')
                participants.append({'id': p_id, 'name': name})
                print(name)

            break

    config['participants'] = participants

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

    print('Updated', config_path, 'with participants.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--names', type=str,
                        help='Comma-separated list of names of people to pair up.')
    parser.add_argument('--schedule', type=str, default='.schedule',
                        help='Path to the schedule file (to generate or read from).')
    parser.add_argument('--n-quotes', type=int, default=0,
                        help='Number of quotes to intersperse with the chats.')
    parser.add_argument('--quotes-db', type=str, default=0,
                        help='Number of fortunes to intersperse with the chats.')
    parser.add_argument('--config', type=str, required=True,
                        help='Path to the config file.')
    parser.add_argument('--setup', action='store_true',
                        help='Reads the people that will get coffee from Slack reactions.')
    parser.add_argument('--run', action='store_true',
                        help='Makes a pairing and posts to Slack.')
    parser.add_argument('--debug', action='store_true',
                        help='Prints message to stdout instead of posting on Slack.')

    opt = parser.parse_args()

    if opt.debug:
        DEBUG = True

    if opt.run:
        execute(opt.config)
    elif opt.setup:
        setup_from_reactions(opt.config)
