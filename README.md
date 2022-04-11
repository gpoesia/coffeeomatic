# coffeeomatic

A Slack bot to arrange 1:1 coffee chats for a group. I've used it in both our research lab (10-15 people) and in the CS PhD program (70+ participants) to pair people every week for an informal coffee chat.

Donut does the same, but it is paid for larger groups (and expensive). Coffeeomatic is free (as in speech and food), with the cost of some setup time.

Roughly, these are the steps you need to set it up:

1- Create an app on Slack. The bot user will need the following OAuth scopes: `chat:write` (post messages), `reactions:read` (see list of reactions to a message), and `channels:history` (get the messages in a channel)
2- Add the bot user to the desired channel on Slack
3- Make a post (with your account for now, though the bot could be modified to do this too) asking people to react to that message if they want to be assigned to chat with other people
4- Create a config file by following the example config. It should crucially contain the Slack channel ID (you can get it from Slack) and the beginning of the message you posted on step 3 (so that the bot can find it and get the reactions). This is an example of a file you can use for the quotes database: [OpenBSD Fortunes File](http://fortunes.cat-v.org/openbsd/).
4- When you want to start making assignments, run `python coffeeomatic.py --setup --config path/to/your/config` to make the bot go find the message you sent on step 4, read the list of reactions, and save all participant names and IDs back to the config file.
5- Then, every time you want to make the bot post a new assignment, run `python coffeeomatic.py --run --config path/to/your/config`. You can do this manually or set up a [cron job](https://wiki.archlinux.org/title/cron) so that you won't forget. You can run it with `--debug` to just print the message that would be sent to stdout, without actually sending anything to Slack or modifying the config file (which would normally be updated with the pairs of people that have already been assigned together in the past).

If you're interested in actually using this too and want more detailed instructions, feel free to create an issue and I will improve this README with screenshots and all that.

Features I'd be interested in for the future:

- Handle an odd number of participants (you can always make it even by removing/adding yourself, but this is not ideal)
- Direct message paired people instead of always posting the list to the channel. Seems like this needs more than `chat:write` and might be more involved with Slack
- Allow two different lists of people, and make pairs of only people from different lists (e.g., senior students vs new students).
