# picks a random line from the given list
def list(lista):
        return(lista[random.randint(0, len(lista)-1)])

# logger of sorts
def logger(who,text):
        call(["date"])
        print("<"+str(who)+"> "+ str(text)+"\n")

def speak(bot,text,whereto):
        global quietmode
        if(quietmode != True):
                bot.say(text,whereto)

def isbanned(bot,nick,whereto):
        if nick.upper in bannedusers:
                speak(bot,list(notallowed),whereto)
                return True
        else:
                return False


