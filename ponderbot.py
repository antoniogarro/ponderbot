#!/usr/bin/python

#Antonio Garro, 2014-2016

#This code, released under the GPL license, is based in a Perl script by Ralph Schuler (http://ralphschuler.ch)
#See https://www.gnu.org/licenses/gpl

try:
    from subprocess32 import Popen, PIPE
    print("subprocess32")
except:
    from subprocess import Popen, PIPE
    print("subprocess")

import re

#CONFIGURATION VALUES:
ENGINE   = "./<engine-binary>"
OPERATOR = "<operator-handle>"
TIMESEAL,SERVER,PORT='./timeseal','167.114.65.195','5000'
MAXGAMES = 0    # 0 for unlimited.
SEEKS    = "seek 1 0 f","seek 2 0 f","seek 3 0 f"
HASH     = "400" #Mb
PONDER   = True
AUTOACCEPT = True
RESTART_ON_NEW = False
QUIT_ON_LOSE = False
DEFAULT_ANSWER  = "I am only a chess program. Contact "+OPERATOR+" if you have any problem."
IGNORE = ["ROBOadmin"]
LOGIN_SCRIPT = """
<engine-account-handle>
<engine-password>

set style 12
set autoflag 1
set mailmess 1
set automail 1
set pgn 0
set shout 0
set seek 0
set bell 0
set cshout 0
set tshout 0
-ch 4
-ch 53
-ch 50
-ch 1
-ch 2
set kibitz 0
set 1 <Engine: ...>
set 2 <Hardware: ...>
set 3
finger
"""

#CONSOLE COLORS:
CMD_COLOR = '\033[95m'
SERVER_COLOR = '\033[94m'
DISCARD_COLOR = '\033[92m'
OUTPUT_COLOR = '\033[93m'
DEFAULT_COLOR = '\033[0m'

class Engine:
  def __init__(self):
    self.__start()
    
  def __start(self):
    self.__e = Popen(ENGINE, stdin=PIPE, stdout=PIPE)
    self.command("uci")
    out = self.output()
    while(out != "uciok"):
      print(OUTPUT_COLOR + "ENGINE -> " + out + DEFAULT_COLOR)
      out = self.output()

    self.command("setoption name Hash value " + HASH)
    #set other UCI options here...
    self.command("isready")
    if(self.output() == "readyok"):
      self.command("ucinewgame")
    return
      
  def command(self,cmd):
    print(CMD_COLOR + "ENGINE <- " + cmd + DEFAULT_COLOR)
    self.__e.stdin.write((cmd + "\n").encode())
    self.__e.stdin.flush()
  
  def output(self):
    return self.__e.stdout.readline().decode().strip()

  def restart(self):
    self.command("quit")
    self.__e.stdout.close()
    self.__e.stdin.close()
    self.__start()

class Server:
  def __init__(self):
    self.__quit = False
    self.__pondering = False
    self.__playedgames = 0
    self.__won = 0
    self.__engine = Engine()
    self.__s = Popen([TIMESEAL,SERVER,PORT], stdin=PIPE, stdout=PIPE)
    self.__seeks = "\n".join(SEEKS)
    
    for s in LOGIN_SCRIPT.split('\n'):
      self.__send(s)
    self.__send(self.__seeks)
  
  def __send(self,msg):
    self.__s.stdin.write((msg + "\n").encode('latin-1'))
    self.__s.stdin.flush()

  def __receive(self):
    return self.__s.stdout.readline().decode('latin-1')

  def __respond(self,tell):
    tell = tell.split()
    nick = re.sub("\(.+\)","",tell[0])
    if(nick == OPERATOR):
      if(tell[3] == "last"):
        self.__quit = True
        self.__send("tell " + OPERATOR + " I'll quit after next game's end.")
      elif (tell[3][0] == '!'):
        self.__send("tell " + OPERATOR + " Ok.")
        self.__send(" ".join(tell[3:])[1:])
    elif nick in IGNORE:
        pass
    else:
      self.__send("tell " + nick +  " "  + DEFAULT_ANSWER)

  def __remaintime(self,style12):
    style12 = style12.split()
    return (str(int(t)*1000) for t in [style12[24],style12[25],style12[21],style12[21]])
    
  def __style12toFEN(self,style12):
    style12 = style12.split()
    rows = [re.sub("(-)+",lambda m: str(len(m.group(0))), s) for s in style12[1:9]]
    
    colortomove = style12[9].lower()
    halfmoveclock = style12[15]
    movenumber = style12[26]
    passedpawn = style12[10]

    self.__lastmove = style12[27][2:4] + style12[27][5:7]
    
    if (passedpawn != "-1"):
      row = "6" if colortomove == "w" else "3"
      column = "abcdefgh"[int(passedpawn)]
      passedpawn = column + row
    else:
      passedpawn = "-"
    
    castle = "".join([c for i,c in enumerate("KQkq") if style12[11:15][i] == '1'])
    if castle == "":
      castle = "-"
    return "/".join(rows) + " " \
         + " ".join([colortomove,castle,passedpawn,halfmoveclock,movenumber])
      
  def __discard_output(self):
    res = self.__engine.output()
    while(res):
      print(DISCARD_COLOR + "Discard > " + res + DEFAULT_COLOR)
      if (res.find("bestmove") > -1):
        return
      res = self.__engine.output()

  def __makeamove(self, style12):
    fen = self.__style12toFEN(style12)
    wtime, btime, winc, binc = self.__remaintime(style12)
    if (not self.__myturn):
      if (PONDER and self.__pondermove):
        self.__engine.command("stop")
        self.__engine.command("position fen " + fen + " moves " + self.__pondermove)
        self.__engine.command("go ponder wtime " + wtime + " btime " + btime + \
                              " winc " + winc + " binc " + binc)
        self.__pondering = True
      return
    elif (self.__pondering):
      self.__pondering = False
      if(self.__lastmove == self.__pondermove):
        self.__engine.command("ponderhit")
      else:
        self.__engine.command("stop")
        self.__discard_output()
        self.__engine.command("position fen " + fen)
        self.__engine.command("go wtime " + wtime + " btime " + btime + \
                              " winc " + winc + " binc " + binc)
    else:
      self.__engine.command("stop")
      self.__engine.command("position fen " + fen)
      self.__engine.command("go wtime " + wtime+" btime " + btime + \
                            " winc " + winc + " binc " + binc)

    out = self.__engine.output()
    pv = ''
    while(out):
      if (out.find("score") > -1):
        pv = out
      print(OUTPUT_COLOR + "ENGINE -> " + out + DEFAULT_COLOR)
      
      if (out.find("bestmove") > -1):
        out = out.split()
        bestmove = out[1]
        if(len(bestmove) > 4):
          bestmove = bestmove[:4] + "=" + bestmove[4:5]
        if(len(out) > 3):
          self.__pondermove = out[3]
        else:
          self.__pondermove = 0
        self.__send(bestmove)
        if pv:
          self.__send("whisper " + pv)
        return
      out = self.__engine.output()
      
  def __endgame(self):
    self.__pondermove = 0
    self.__engine.command("stop")
    if (self.__pondering):
      self.__discard_output()
      self.__pondering = False
    if (self.__quit or (MAXGAMES and self.__playedgames >= MAXGAMES)):
      self.__send("exit")
      return
    elif (RESTART_ON_NEW):
      self.__engine.restart()
    else:
      self.__engine.command("ucinewgame")
    self.__send(self.__seeks)
         
  def main(self):
    line = self.__receive()
    style12re = "<12> ([rnbqkpRNBQKP-]{8} ){8}(W|B) ([0-9-]{1,2} ){6}\d+ (.+ ){2}([0-9-]{1,4} ){8}(none|[rnbqkpRNBQKP]/..-..(\+|=\D)?|o-o(-o)?) \(\d+:\d+\) (none|\D?.?x?..(\+|=\D)?|O-O(-O)?) . . ."
    while(line):
      line = self.__receive()
      print(SERVER_COLOR + line.strip() + DEFAULT_COLOR)
      if (line.find("tells you") > -1 or line.find("says") > -1):
        self.__respond(line)
        pass

      elif (line.find("Finger of") > -1):
        self.__handle = re.search("Finger of ([A-z]+)", line).group(1)

      elif (re.search(style12re,line)):
        style12 = line.split()
        self.__myturn = self.__mycolor == style12[9].lower()
        self.__makeamove(line)

      elif (line.find("Creating: ") > -1):
        self.__playedgames += 1
        gamedata = line.split()
        self.__mycolor = "w" if gamedata[1] == self.__handle else "b"
        self.__send("tell " + OPERATOR + " New game (" + str(self.__playedgames) + \
                    ") started with color " + self.__mycolor + " (" + str(self.__won) + " won)")
        self.__pondermove = 0
        
        #Here, game-dependent UCI options can be set:
        try:
          ratingdiff = int(gamedata[2][1:5]) - int(gamedata[4][1:5])
        except ValueError:
          ratingdiff = 100
        contempt = 0.1*ratingdiff if self.__mycolor == 'w' else -0.1*ratingdiff
        self.__engine.command("setoption name Contempt value " + str(contempt))

      elif (re.search("rating(s)? adjustment", line) \
         or line.find("aborted") > -1 \
         or line.find("Auto-flagging.") > -1):
        self.__endgame()

      elif (AUTOACCEPT and line.find("Challenge:") > -1):
        self.__send("accept")
      
      else:
        result = re.search("{Game .+ \(.+ vs\. .+\) .+} (.-.)", line)
        if result:
          if (self.__mycolor == 'w' and result.group(1) == '1-0')\
          or (self.__mycolor == 'b' and result.group(1) == '0-1'):
            self.__won += 1
          elif QUIT_ON_LOSE:
            self.__send("exit")

if __name__ == "__main__":
  Server().main()
