Build-a-Bot Workshop
====================

If you're an organisation that contributes collection records to Trove you can use this code to build your own Twitter bot that responds to user queries and tweets random collection items.

### Requirements

* Python
* [python-twitter](https://github.com/bear/python-twitter) and its dependencies

### Establishing your credentials

To set up your bot you need to create a Twitter account and then generate the necessary authentication keys for both Twitter and Trove.

1. Get a Trove API key by following [these instructions](http://trove.nla.gov.au/general/api).
2. Once you have the key insert it in credentials.py.
3. Decide on a name for your bot and insert it in the appropriate place in trovebot.py (without the @).
4. Sign up for a Twitter account in the name of your bot.
5. Go to the [Twitter Developer Site](https://dev.twitter.com/) and sign in using your bot's details.
6. Click on 'Create an App' and fill out and submit the form. You don't need a callback url.
7. On the 'Settings' tab under 'Application type' select the radio button next to 'Read and Write'. Click the 'Update' button.
8. On the 'Details' tab click the 'Create my access token' button.
9. If your access token details don't appear, reload the page.
10. Copy the following values to credentials.py: 'Consumer Key', 'Consumer Secret', 'Access Token', and 'Access Token Secret'.

### Identifying your collection

To limit the bot's tweets to your own collection you need to know your organisation's NUC symbol.

1. Go to the [Australian Libraries Gateway](http://www.nla.gov.au/libraries/index.html).
2. Click on 'Find a library' and search for your organisation. Note that there may be more than one entry -- perhaps one for your library and one for your collection or repository.
3. Click on the 'More details' button.
4. Look for the NUC symbol and copy it. It may be just a four letter code, or a four letter code followed by a colon and further letters eg: 'AMOA' or 'AMOA:C'.
5. Copy the NUC symbol to the appropriate place in trovebot.py.

### Deploying your bot

You don't need anything fancy to host your bot, just a machine permanently connected to the net. If you're deploying to a server, you might need to set the path values in file_locations_prod.py. If that's the case, don't upload file_locations_dev.py.

### Activating your bot

In a terminal go to the directory containing your bot's files.

To make it reply to queries enter:

    python trovebot.py reply

To make it tweet a random collection item enter:

    python trovebot.py random

You probably want to set these up to run at regular intervals using something like cron. I tend to run the 'reply' script every five minutes, and the 'random' script every few hours.

### Basic bot behaviours

* Include the word 'hello' in a message to your bot to receive a greeting and a random collection item.
* Any other message will be treated as a query and will be sent off to the Trove API to look for matching results.
* To receive any old random collection item, just tweet your bot the hashtag '#luckydip' and nothing else.

### Modifying your bot query

By default, your bot tweets the first (ie most relevant) matching result back to you. To change this you can:

* Include the hashtag '#luckydip' to receive a random item from the matching results.

By default, the search terms you supply are sent directly to the Trove API without any modification. To change this you can:

* Include the hashtag '#any' to search for items that match *any* of your search terms. This is the same as adding an 'OR' between your terms.

### Credits

Built by @wragge using the [Trove API](http://trove.nla.gov.au/general/api) and the Twitter API.

Released under CC0 licence.
