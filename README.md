Ponderbot.py
============

A bot for letting UCI chess engines play on FICS, written in Python.


Usage
-----

Configure the bot by changing the CONFIGURATION VALUES at the beginning of the file. You may want to specify:

 - ENGINE: path to the engine binary.
 - OPERATOR: FICS handle (*nick*) of the operator, who will be allowed to give the engine commands through tells.
 - TIMESEAL: path to the timeseal binary (for instance, ./zseal).
 - SEEKS: three possible seek parameters, to be sent by the engine upon login and after every game's end.
 - HASH: size for the hash table (in MB), if supported by the engine.
 - PONDER: whether the engine will be allowed to think during the oponnent's time.
 - AUTOACCEPT: whether to accept every challenge received.
 - RESTART_ON_NEW: whether to restart the engine after every match.
 - QUIT_ON_LOSE: whether to quit after losing (useful for debugging purposes).
 - DEFAULT ANSWER: polite answer to be sent to other players when they attempt to chat.
 - IGNORE: players whose tells will be ignored.
 - LOGIN_SCRIPT: series of commands to be sent to the server upon login. The first line should be the engine's FICS handle. To play as guest, just leave it as "g". The second line should be the account's password (plain text for now...).
 
Once logged in, the OPERATOR (and only him) may send commands to the engine by preceding tells with '!', such as: "tell <engine_handle> !command". Some examples:

	tell Claudiae !unseek
	tell Claudiae !seek 15 15 r f
	tell Claudiae !quit

A new, open source version of timeseal, courtesy of Felipe Bergo, may be obtained [here](https://github.com/fbergo/zseal)


License
-------

Ponderbot.py is released under the GPL license. See [https://www.gnu.org/licenses/gpl](https://www.gnu.org/licenses/gpl) for the details.


Thanks
------

To [Ralph Schuler](http://ralphschuler.ch) for inspiring this project with his Perl UCI FICS bot.

To Felipe Bergo, for zseal.
