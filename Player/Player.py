import argparse
import socket
import sys
import time

class Player:
    myName = ''
    opponentName = ''
    myStackSize = 0 #this may not always be up to date
    opponentStackSize = 0 #this may not always be up to date
    bigBlind = 0
    totalNumHands = 0
    handId = 0
    myHand = list()
    potSize = 0
    numBoardCards = 0
    boardCards = list()
    myBet = 0
    opponentBet = 0
    
    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()
        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if not data:
                print "Gameover, engine disconnected."
                break

            # Here is where you should implement code to parse the packets from
            # the engine and act on it. We are just printing it instead.
            print data

            # When appropriate, reply to the engine with a legal action.
            # The engine will ignore all spurious responses.
            # The engine will also check/fold for you if you return an
            # illegal action.
            # When sending responses, terminate each response with a newline
            # character (\n) or your bot will hang!
            self.parsePacket(data) #parse the packet
            time.sleep(2)
        # Clean up the socket.
        s.close()

    #acts on given packet
    def parsePacket(self, data):
        words = data.split() #split packet string at each space to produce array of words
        packetType = words[0] #the first word represents the type of packet
        if(packetType == "GETACTION"):
            self.handlePacketGetAction(words)
            return
        if(packetType == "REQUESTKEYVALUES"):
            self.handlePacketRequestKeyValues()
            return
        if(packetType == "NEWGAME"):
            self.handlePacketNewGame(words)
            return
        if(packetType == "NEWHAND"):
            self.handlePacketNewHand(words)
            return
        self.handlePacketUnknownType()

    #updates potSize, numBoardCards, boardCards, myBet, opponentBet
    def handlePacketGetAction(self, words):
        self.potSize = int(words[1])
        self.numBoardCards = int(words[2])
        del self.boardCards[:] #clear board cards list
        for word in range(3,3 + self.numBoardCards): #add board cards to list
            self.boardCards.append(self.parseCard(words[word]))
        
        numPerformedActions = int(words[3 + self.numBoardCards]) #get the number of actions performed since my last action
        for word in range(4 + self.numBoardCards, 4 + self.numBoardCards + numPerformedActions): #parse every performed action
            self.parsePerformedAction(words[word])

        canBet = False
        minBet = 0
        maxBet = 0
        canCall = False
        canCheck = False
        canFold = False
        canRaise = False
        minRaise = 0
        maxRaise = 0
        numLegalActions = int(words[4 + self.numBoardCards + numPerformedActions])
        for word in range(5 + self.numBoardCards + numPerformedActions, 5 + self.numBoardCards + numPerformedActions + numLegalActions):
            subWords = words[word].split(':')
            if(subWords[0] == "BET"):
                canBet = True
                minBet = int(subWords[1])
                maxBet = int(subWords[2])
                next
            if(subWords[0] == "CALL"):
                canCall = True
                next
            if(subWords[0] == "CHECK"):
                canCheck = True
                next
            if(subWords[0] == "FOLD"):
                canFold = True
                next
            if(subWords[0] == "RAISE"):
                canRaise = True
                minRaise = int(subWords[1])
                maxRaise = int(subWords[2])
                next

        print "Pot Size: ", self.potSize
        print "My Bet: ", self.myBet
        print "Opponent Bet: ", self.opponentBet
        print "Can Bet: ", canBet, ":", minBet, ":", maxBet
        print "Can Call: ", canCall
        print "Can Fold: ", canFold
        print "Can Raise: ", canRaise, ":", minRaise, ":", maxRaise
        print "Can Check: ", canCheck

        s.send("CHECK\n") #default behaviour of the example player
    
    #handles actions performed between GetAction packets
    def parsePerformedAction(self, performedAction):
        words = performedAction.split(':')
        if(words[0] == "POST"):
            self.handlePerformedActionPost(words)
            return
        if(words[0] == "CALL"):
            self.handlePerformedActionCall(words)
            return
        if(words[0] == "RAISE"):
            self.handlePerformedActionRaise(words)
            return
        if(words[0] == "BET"):
            self.handlePerformedActionBet(words)
            return
    
    #updates myBet or opponentBet
    def handlePerformedActionBet(self, words):
        if(words[2] == self.myName):
            self.myBet = self.myBet + int(words[1])
            return
        self.opponentBet = self.opponentBet + int(words[1])
        
    #updates myBet or opponentBet
    def handlePerformedActionRaise(self, words):
        if(words[2] == self.myName):
            self.myBet = int(words[1])
            return
        self.opponentBet = int(words[1])

    #updates myBet or opponentBet - but doesn't agree with documentation
    def handlePerformedActionCall(self, words):
        if(words[1] == self.myName):
            self.myBet = self.opponentBet
            return
        self.opponentBet = self.myBet

    #updates either myBet or opponentBet based on the blinds
    def handlePerformedActionPost(self, words):
        if(words[2] == self.myName):
            self.myBet = int(words[1])
            return
        self.opponentBet = int(words[1])

    #updates myName, opponentName, myStackSize, bigBlind, totalNumHands
    def handlePacketNewGame(self, words):
        self.myName = words[1]
        self.opponentName = words[2]
        self.myStackSize = int(words[3])
        self.bigBlind = int(words[4])
        self.totalNumHands = int(words[5])

    #updates handId, myHand, myStack, opponentStack, myBet
    def handlePacketNewHand(self, words):
        self.handId = int(words[1])
        del self.myHand[:] #clear current hand
        self.myHand.append(self.parseCard(words[3])) #add cards to hand
        self.myHand.append(self.parseCard(words[4]))
        self.myHand.append(self.parseCard(words[5]))
        self.myHand.append(self.parseCard(words[6]))
        self.myStack = int(words[7]) #update myStack
        self.opponentStack = int(words[8]) #update opponentStack
        self.myBet = 0 #reset myBet
        self.opponentBet = 0 #reset opponentBet
        del self.myHand[:] #reset myHand
        del self.boardCards[:] #reset boardCards
        self.numBoardCards = 0 
        self.potSize = 0; #reset potSize
        
    def handlePacketRequestKeyValues(self):
        s.send("FINISH\n") #default behaviour of example player

    def handlePacketUnknownType(self):
        print "Unhandled packet"

    #takes string such as "Qs" and returns tuple of (11,s)
    def parseCard(self, cardString):
        number = cardString[0]
        if(number == "T"):
            number = 10
        if(numbesr == "J"):
            number = 11
        if(number == "Q"):
            number = 12
        if(number == "K"):
            number = 13
        if(number == "A"):
            number = 14
        return (number, cardString[1])
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    print 'Connecting to %s:%d' % (args.host, args.port)
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        print 'Error connecting! Aborting'
        exit()

    bot = Player()
    bot.run(s)
