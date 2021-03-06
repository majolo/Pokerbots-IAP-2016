import argparse
import socket
import sys
import time
import PokerPhysics as PP
import handEvalTable as evalTable
import Pokerini
import Simulation
import math
import WhoIsIt

class Player:

    debugPrint = False
    iAgreeWithBet = False 
    opponentAgreesWithBet = False
    myName = ''
    opponentName = ''
    myStackSize = 0 #this may not always be up to date
    opponentStackSize = 0 #this may not always be up to date
    bigBlind = 0 #big blind specified by engine
    totalNumHands = 0 #the total number of hands to be played this game
    totalTime = 0 #updated on NewGame packet, stores total time allocated for game
    handId = 0 #the hand Id specified by the engine
    myHand = list() #list of tuples representing cards in my hand
    potSize = 0 #the potSize specified by the engine (should equal sum of pots and bets)
    numBoardCards = 0 #the number of cards of the board
    boardCards = list() #list of tuples representing cards on the board
    myPot = 0 #keeps track of my pot (should be the same as opponentPot)
    opponentPot = 0 #keeps track of opponent pot
    myBet = 0 #keeps track of my current bet
    opponentBet = 0 #keeps track of current opponent bet
    cardsChanged = True
    minus50Time = 0 #keeps track of the time 50 hands ago
    totalNumSimulations = 0 # Average numSimulations * number of hands played
    simulationWinChance = 0
    pokeriniRank = 0
    expectedTimePerHand = 0 #calculated on NewGame packet. = original time bank / total num hands to play
    timeBank = 0
    preflopBetLimit = 0
    numSimulations = 40
    numRaises = 0
    maxRaises = 0

    opponentRound0Folds = 0
    opponentRound1Folds = 0
    opponentRound2Folds = 0
    opponentRound3Folds = 0

    checkCallThresh = 0.0
    raiseLinearlyThresh = 0.6
    raiseFullThresh = 1.0
    round0CheckCallThresh = 0.0
    round0RaiseLinearlyThresh = 0.5
    round0RaiseFullThresh = 1.0
    preflopMinRaiseLimit = 50
    preflopMaxRaiseLimit = 200

    def loadParametersFromFile(self):
        with open('PlayParameters.txt') as f:
            for x in f:
                if(x[0:15] == "checkCallThresh"):
                    self.checkCallThresh = float(x[15:-1])
                    print "checkCallThresh " + str(self.checkCallThresh)
                if(x[0:19] == "raiseLinearlyThresh"):
                    self.raiseLinearlyThresh = float(x[19:-1])
                    print "raiseLinearlyThresh " + str(self.raiseLinearlyThresh)
                if(x[0:15] == "raiseFullThresh"):
                    self.raiseFullThresh = float(x[15:-1])
                    print "raiseFullThresh " + str(self.raiseFullThresh)
                if(x[0:21] == "round0CheckCallThresh"):
                    self.round0CheckCallThresh = float(x[21:-1])
                    print "round0CheckCallThresh " + str(self.round0CheckCallThresh)
                if(x[0:25] == "round0RaiseLinearlyThresh"):
                    self.round0RaiseLinearlyThresh = float(x[25:-1])
                    print "round0RaiseLinearlyThresh " + str(self.round0RaiseLinearlyThresh)
                if(x[0:21] == "round0RaiseFullThresh"):
                    self.round0RaiseFullThresh = float(x[21:-1])
                    print "round0RaiseFullThresh " + str(self.round0RaiseFullThresh)
                if(x[0:20] == "preflopMinRaiseLimit"):
                    self.preflopMinRaiseLimit = int(x[20:-1])
                    print "preflopMinRaiseLimit " + str(self.preflopMinRaiseLimit)
                if(x[0:20] == "preflopMaxRaiseLimit"):
                    self.preflopMaxRaiseLimit = int(x[20:-1])
                    print "preflopMaxRaiseLimit " + str(self.preflopMaxRaiseLimit)
            f.close()

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
            #if self.debugPrint:
            print data
            # When sending responses, terminate each response with a newline character (\n) or your bot will hang!
            self.parsePacket(data)
            if self.debugPrint: print ""
        # Clean up the socket.
        s.close()

    #If both players agree on bet, moves bet to pot
    def updatePot(self):
        if(self.iAgreeWithBet and self.opponentAgreesWithBet):
            self.myPot = self.myPot + self.myBet
            self.myBet = 0
            self.opponentPot = self.opponentPot + self.opponentBet
            self.opponentBet = 0
            self.iAgreeWithBet = False
            self.opponentAgreesWithBet = False

    def getExpectedTimeBank(self): #returns what the time bank should be at the end of the hand if we are playing exactly to time
        return self.totalTime - self.expectedTimePerHand * self.handId

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
        if(packetType == "HANDOVER"):
            self.handlePacketHandOver(words)
            return
        self.handlePacketUnknownType()

    #updates potSize, numBoardCards, boardCards, myBet, opponentBet
    def handlePacketGetAction(self, words):
        actionStartTime = time.time() #store the time that the request was made
        self.potSize = int(words[1])
        self.numBoardCards = int(words[2])
        del self.boardCards[:] #clear board cards list
        for word in range(3,3 + self.numBoardCards): #add board cards to list
            self.boardCards.append(self.parseCard(words[word]))
        
        numPerformedActions = int(words[3 + self.numBoardCards]) #get the number of actions performed since my last action
        for word in range(4 + self.numBoardCards, 4 + self.numBoardCards + numPerformedActions): #parse every performed action
            self.parsePerformedAction(words[word]) #update variables depending on performedActions
            self.updatePot() #update the pot

        canBet = False
        minBet = 0
        maxBet = 0
        canCall = False
        canCheck = False
        canFold = False
        canRaise = False
        minRaise = 0
        maxRaise = 0
        #parse all legal actions
        numLegalActions = int(words[4 + self.numBoardCards + numPerformedActions])
        for word in range(5 + self.numBoardCards + numPerformedActions, 5 + self.numBoardCards + numPerformedActions + numLegalActions):
            subWords = words[word].split(':')
            if(subWords[0] == "BET"):
                canBet = True
                minBet = int(subWords[1])
                maxBet = int(subWords[2])
                continue
            if(subWords[0] == "CALL"):
                canCall = True
                continue
            if(subWords[0] == "CHECK"):
                canCheck = True
                continue
            if(subWords[0] == "FOLD"):
                canFold = True
                continue
            if(subWords[0] == "RAISE"):
                canRaise = True
                minRaise = int(subWords[1])
                maxRaise = int(subWords[2])
                continue 

        self.timeBank = float(words[5 + self.numBoardCards + numPerformedActions + numLegalActions])

        response = self.choosePlay(canBet, minBet, maxBet, canCall, canCheck, canFold, canRaise, minRaise, maxRaise, actionStartTime)
        s.send(response+"\n")
        actionFinishTime = time.time() #store the time that we responsed
        #print out details that will be used to make decision on move
        if self.debugPrint:
            print "Hand Number: ", self.handId
            print "My Bet: ", self.myBet
            print "Opponent Bet: ", self.opponentBet
            print "My Pot: ", self.myPot
            print "Opponent Pot: ", self.opponentPot
            print "Preflop bet limit: ", self.preflopBetLimit
            print "Response time: ", (actionFinishTime - actionStartTime)
            print "Timebank: ", self.timeBank
            print "Expected Timebank: ", self.getExpectedTimeBank()
            print "Round 0 folds: " + str(self.opponentRound0Folds)
            print "Round 1 folds: " + str(self.opponentRound1Folds)
            print "Round 2 folds: " + str(self.opponentRound2Folds)
            print "Round 3 folds: " + str(self.opponentRound3Folds)

        print "My Hand: ", self.myHand
        print "Board Cards: ", self.boardCards
        print "Response: " + response


        #check that the pots and bets agree with the specified pot size
        if(self.myBet + self.myPot + self.opponentBet + self.opponentPot != self.potSize):
            print "ERROR IN POT SIZES"
            raw_input("Press anykey to continue")
        
        #x = raw_input('Response: ') #uncomment to enter responses by hand
        #s.send(x+"\n")
    
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
        if(words[0] == "CHECK"):
            self.handlePerformedActionCheck(words)
            return
        if(words[0] == "DEAL"):
            self.handlePerformedActionDeal(words)
            return
        if(words[0] == "FOLD"):
            self.handlePerformedActionFold(words)
            return

    def handlePerformedActionFold(self, words):
        if(words[1] == self.opponentName):
            if(self.numBoardCards == 0):
                self.opponentRound0Folds += 1
            if(self.numBoardCards == 3):
                self.opponentRound1Folds += 1
            if(self.numBoardCards == 4):
                self.opponentRound2Folds += 1
            if(self.numBoardCards == 5):
                self.opponentRound3Folds += 1

    def handlePerformedActionDeal(self, words):
        self.cardsChanged = True

    def handlePerformedActionCheck(self, words):
        if(words[1] == self.myName):
            self.iAgreeWithBet = True
            return
        self.opponentAgreesWithBet = True
        self.maxRaises +=1
    
    #updates myBet or opponentBet
    def handlePerformedActionBet(self, words):
        if(words[2] == self.myName):
            self.myBet = int(words[1])
            self.iAgreeWithBet = True
            self.opponentAgreesWithBet = False
            return
        self.opponentBet = int(words[1])
        self.iAgreeWithBet = False
        self.opponentAgreesWithBet = True
        self.numRaises += 1
        self.maxRaises +=1

        
    #updates myBet or opponentBet
    def handlePerformedActionRaise(self, words):
        if(words[2] == self.myName):
            self.myBet = int(words[1])
            self.iAgreeWithBet = True
            self.opponentAgreesWithBet = False
            return
        self.opponentBet = int(words[1])
        self.iAgreeWithBet = False
        self.opponentAgreesWithBet = True
        self.numRaises += 1
        self.maxRaises +=1

    #updates myBet or opponentBet - but doesn't agree with documentation
    def handlePerformedActionCall(self, words):
        if(words[1] == self.myName):
            self.myBet = self.opponentBet
            self.iAgreeWithBet = True
            return
        self.opponentBet = self.myBet
        self.opponentAgreesWithBet = True
        self.maxRaises +=1

    #updates either myBet or opponentBet based on the blinds
    def handlePerformedActionPost(self, words):
        if(words[2] == self.myName):
            self.myBet = int(words[1])
            self.iAgreeWithBet = False
            return
        self.opponentBet = int(words[1])
        self.opponentAgreesWithBet = False

    def handlePacketHandOver(self, words):
        self.numBoardCards = int(words[3])
        
        numPerformedActions = int(words[4 + self.numBoardCards]) #get the number of actions performed since my last action
        for word in range(5 + self.numBoardCards, 5 + self.numBoardCards + numPerformedActions): #parse every performed action
            self.parsePerformedAction(words[word]) #update variables depending on performedActions
            self.updatePot() #update the pot

        if(self.handId % 50 == 0):
            print "I think we are playing against: " + WhoIsIt.whoIsIt(self.opponentRound0Folds, self.opponentRound1Folds, self.opponentRound2Folds, self.opponentRound3Folds, self.handId)

    #updates myName, opponentName, myStackSize, bigBlind, totalNumHands
    def handlePacketNewGame(self, words):
        self.myName = words[1]
        self.opponentName = words[2]
        self.myStackSize = int(words[3])
        self.bigBlind = int(words[4])
        self.totalNumHands = int(words[5])
        self.timeBank = float(words[6])
        self.totalTime = self.timeBank
        self.minus50Time = self.totalTime
        self.expectedTimePerHand = self.timeBank / self.totalNumHands # calculate the expected time per hand
        self.iAgreeWithBet = False
        self.opponentAgreesWithBet = False

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
        self.timeBank = float(words[9])
        self.myBet = 0 #reset myBet
        self.opponentBet = 0 #reset opponentBet
        self.myPot = 0 #reset myPot
        self.opponentPot = 0 #reset opponentPot
        del self.boardCards[:] #reset boardCards
        self.numBoardCards = 0 
        self.potSize = 0 #reset potSize
        self.iAgreeWithBet = False
        self.opponentAgreesWithBet = False
        self.cardsChanged = True
        self.numRaises = 0
        self.maxRaises = 0
        if (self.handId % 10 == 0) and (self.handId != 1000):
            self.numSimulations = self.calcNumSimulations()
            print "NumSimulations: ", self.numSimulations
        
    def handlePacketRequestKeyValues(self):
        if self.debugPrint: print "FINISHED"
        #handEvalDict.clear() #MUST CLEAR THE DICTIONARY OR ENGINE COMPLAINS!
        s.send("FINISH\n") #default behaviour of example player

    def handlePacketUnknownType(self):
        if self.debugPrint: print "Unhandled packet"

    #takes string such as "Qs" and returns tuple of (11,s)
    def parseCard(self, cardString):
        number = cardString[0]
        if(number == "T"):
            number = 10
        if(number == "J"):
            number = 11
        if(number == "Q"):
            number = 12
        if(number == "K"):
            number = 13
        if(number == "A"):
            number = 14
        return (int(number), cardString[1])

    def choosePlay(self, canBet, minBet, maxBet, canCall, canCheck, canFold, canRaise, minRaise, maxRaise, actionStartTime):
        self.updateHandRanking() #update hand rankings

        print 'numRaises/maxRaises: ' +  str(self.numRaises) + '/' + str(self.maxRaises)

        if(self.numBoardCards == 0):
            if self.debugPrint: print "Pokerini Rank: " + str(self.pokeriniRank)
            if(self.pokeriniRank < 0.3): #if we are in the checkFold region
                return self.checkFold(canCheck)
            if(self.pokeriniRank < 0.6): #if we are in the checkCall region
                return self.checkCallFold(canCheck, canCall, self.pokeriniRank)
            if(self.pokeriniRank > self.round0RaiseFullThresh): #if we are in the raise full region (above 65%) 
                return self.betRaise(1.0, canBet, minBet, maxBet, canRaise, minRaise, maxRaise, canCheck, canCall) #raise/bet max
            #we are in the raise linearly region
            raisePercentage = self.calculateRaisePercentage(25, self.pokeriniRank, 0.6)
            print 'Raise Percentage: ', raisePercentage
            return self.betRaise(raisePercentage, canBet, minBet, maxBet, canRaise, minRaise, maxRaise, canCheck, canCall) #raise/bet by correct percentage

        if(self.numBoardCards >= 3):
            winChanceCompensated = self.simulationWinChance
            if self.maxRaises > 0:
                winChanceCompensated  -= (0.2 * self.numRaises / self.maxRaises)
            if winChanceCompensated < 0:
                winChanceCompensated = 0

            if self.debugPrint: print "Simulation Win Chance: " + str(self.simulationWinChance)
            if winChanceCompensated < (0.5 - 0.1 * (self.numBoardCards - 3)): #if we are in the checkCallFold region
                return self.checkFold(canCheck)
            tempRaiseThresh = 0.6 + 0.05*(self.numBoardCards - 3)
            if(winChanceCompensated < tempRaiseThresh ): #if we are in the checkCall region
                return self.checkCallFold(canCheck, canCall, winChanceCompensated)
            if(self.simulationWinChance > 1.0): #if we are in the raise full region
                return self.betRaise(1.0, canBet, minBet, maxBet, canRaise, minRaise, maxRaise, canCheck, canCall) #raise/bet maxf
            #we are in the raise linearly region
            raisePercentage = self.calculateRaisePercentage(10, winChanceCompensated, tempRaiseThresh)
            print 'Raise Percentage: ',  raisePercentage
            return self.betRaise(raisePercentage, canBet, minBet, maxBet, canRaise, minRaise, maxRaise, canCheck, canCall) #raise/bet by correct percentage

    def calculateRaisePercentage(self, myLambda, winChance, raiseThresh):
        return 1 - math.exp(-1 * myLambda * (winChance - raiseThresh))

    def updateHandRanking(self):
        if(self.cardsChanged == True):
            if(self.numBoardCards == 0): #preflop
                self.pokeriniRank = Pokerini.pokeriniLookup(self.myHand, pokeriniDict)
                self.calculatePreflopBetLimit()
            if(self.numBoardCards >= 3):#postflop
                #self.simulationWinChance = Simulation.simulate(self.myHand, self.boardCards, self.numBoardCards, 200, handEvalDict, translationDict)
                self.simulationWinChance = Simulation.simulateOld(self.myHand, self.boardCards, self.numBoardCards, self.numSimulations)
        self.cardsChanged = False

    def calculatePreflopBetLimit(self): #calculate maximum raise/bet in preflop stage
        if(self.pokeriniRank >= self.round0RaiseLinearlyThresh):
            self.preflopBetLimit = int(self.preflopMinRaiseLimit + (self.preflopMaxRaiseLimit - self.preflopMinRaiseLimit) 
                                    * (self.pokeriniRank - self.round0RaiseLinearlyThresh) / (self.round0RaiseFullThresh - self.round0RaiseLinearlyThresh))
            if(self.pokeriniRank >= self.round0RaiseFullThresh):
                self.preflopBetLimit = 400

    def betRaise(self, percentage, canBet, minBet, maxBet, canRaise, minRaise, maxRaise, canCheck, canCall):
        if(percentage > 1.0):
            percentage = 1.0
        if(percentage < 0.0):
            percentage = 0.0

        if(canBet):
            betAmount = round(percentage*(maxBet - minBet) + minBet)
            if(self.numBoardCards == 0 and betAmount >= self.preflopBetLimit): #make sure our bet is not above our preflop limit
                betAmount = self.preflopBetLimit
            if(betAmount < minBet):
                return self.checkCall(canCheck, canCall)
            return "BET:"+str(betAmount)

        if(canRaise):
            raiseAmount = round(percentage*(maxRaise - minRaise) + minRaise)
            if(self.numBoardCards == 0 and raiseAmount >= self.preflopBetLimit): #make sure our raise is not above our preflop limit
                raiseAmount = self.preflopBetLimit
            if(raiseAmount < minRaise):
                return self.checkCall(canCheck, canCall)
            return "RAISE:"+str(raiseAmount)
        return self.checkCall(canCheck, canCall) #if you cant betRaise, checkCall

    def checkFold(self, canCheck):
        if(canCheck):
            return "CHECK"
        return "FOLD"

    # this function will check if possible, otheriwise, call up to a limit, otherwise fold
    def checkCallFold(self, canCheck, canCall, winChance):
        if(canCheck):
            return "CHECK"
        EV = winChance * (self.potSize + (self.opponentBet - self.myBet)) - (self.opponentBet - self.myBet)
        if(EV > 0):
            return "CALL"
        return "FOLD"

    def checkCall(self, canCheck, canCall):
        if(canCall):
            return "CALL"
        if(canCheck):
            return "CHECK"
        return self.checkFold(canCheck) #if you can't checkCall, checkFold

    def calcNumSimulations(self):
        self.totalNumSimulations += self.numSimulations * 10
        timePerHand = (self.totalTime - self.timeBank) / (self.handId-1)
        timeLeftPerHand = self.timeBank / (self.totalNumHands - (self.handId-1))
        meanSimulations = self.totalNumSimulations / (self.handId -1)
        print "timeLeftPerHand: ", timeLeftPerHand
        print "timePerHand", timePerHand
        if self.handId > self.totalNumHands - 20:
            safetyFactor = 0.60
        elif self.handId > self.totalNumHands - 60:
            safetyFactor = 0.80
        else:
            safetyFactor = 0.95
        return int(meanSimulations * safetyFactor * ( timeLeftPerHand / timePerHand ))

if __name__ == '__main__':
    start =time.time()
    bot = Player()
    #bot.loadParametersFromFile()
    pokeriniDict = Pokerini.pokeriniInitialise()
    #PP.processDumpFile()
    #evalTable.createEvalCSV()

    '''
    handEvalDict = evalTable.loadHandEval()
    translationDict = evalTable.loadTranslationDict()
    '''

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
    end =time.time()
    print end -start
    bot.run(s)
