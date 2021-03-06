import PokerPhysics as PP
import Pokerini
import Simulation
import os
import math

def median(lst):
    lst = sorted(lst)
    if len(lst) < 1:
            return None
    if len(lst) %2 == 1:
            return lst[((len(lst)+1)/2)-1]
    else:
            return float(sum(lst[(len(lst)/2)-1:(len(lst)/2)+1]))/2.0

def parseCard(cardString):
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

def parseHand(words, length):
    if length == 1:
        return [parseCard(words[1:-1])]
    hand = []
    for x in range(0,length):
        if x == 0:
            hand.append(parseCard(words[x][1:]))
            continue
        if x == length-1:
            hand.append(parseCard(words[x][:-1]))
            continue
        hand.append(parseCard(words[x]))
    return hand

pokeriniDict = Pokerini.pokeriniInitialise()

print "*********************************************************************"


teamID = {}

for fn in os.listdir('hands'):
    #print (fn)
    #Pokerini initialised
    #Open and process the file
    #f = open('process.txt', 'r')
    if fn == ".DS_Store": continue

    print fn

    f = open("hands/" + fn, 'r')
    x = f.readlines()

    #print x[0]

    #Split the lines into each hand
    start = 0
    end = 0
    hand = 1
    handsDict = {}
    lineNum = len(x)
    for i in range(0,lineNum):
        line = x[i]
        if line == '\n':
            end = i
            handsDict[hand] = x[start:end]
            start = i+1
            hand += 1

    #Rip team names from line 1
    team1 = x[0].split()[4]
    team2 = x[0].split()[6]

    #Will use this again at some point
    """handInfo = {}
    for hand in handsDict:
        handInfo[hand] = {}
        handInfo[hand][team1] = {"round0":{"hand":None,"betSize":0,"winProb":None}, "round1":{"hand":None,"betSize":0,"winProb":None}, "round2":{"hand":None,"betSize":0,"winProb":None}, "round3":{"hand":None,"betSize":0,"winProb":None}}
        handInfo[hand][team2] = {"round0":{"hand":None,"betSize":0,"winProb":None}, "round1":{"hand":None,"betSize":0,"winProb":None}, "round2":{"hand":None,"betSize":0,"winProb":None}, "round3":{"hand":None,"betSize":0,"winProb":None}}
    """

    #Initialise exit and win dictionarys 
    team1Exits = {"showdown": 0, "round0fold": 0, "round1fold": 0, "round2fold": 0, "round3fold": 0}
    team2Exits = {"showdown": 0, "round0fold": 0, "round1fold": 0, "round2fold": 0, "round3fold": 0}
    team1Wins = {'wins': 0, 'totalScore': 0, "listWins": []}
    team2Wins = {'wins': 0, 'totalScore': 0, "listWins": []}

    team1folds0 = []
    team2folds0 = []

    team1folds1 = []
    team2folds1 = []

    team1folds2 = []
    team2folds2 = []

    team1folds3 = []
    team2folds3 = []

    team1hand = []
    team2hand = []

    #Parse the data from hands into a useful format
    for hand in handsDict:

        roundNum = 0
        for line in handsDict[hand]:
            split = line.split()

            if split[0] == "Dealt":
                handParse = parseHand(split[3:], 4)
                team = split[2]
                if team == team1: team1hand = handParse
                if team == team2: team2hand = handParse

            if split[1] == "folds":
                team = split[0]
                if team == team1: 
                    team1Exits["round" + str(roundNum) + "fold"] += 1
                    if roundNum == 0:
                        team1folds0.append(Pokerini.pokeriniLookup(team1hand, pokeriniDict))
                if team == team2: 
                    team2Exits["round" + str(roundNum) + "fold"] += 1
                    if roundNum == 0:
                        team2folds0.append(Pokerini.pokeriniLookup(team2hand, pokeriniDict))
                continue
            if split[1] == "wins":
                team = split[0]
                if team == team1: 
                    team1Wins["wins"] += 1
                    team1Wins["totalScore"] += int(split[4][1:-1])
                    team1Wins["listWins"].append(int(split[4][1:-1]))
                if team == team2: 
                    team2Wins["wins"] += 1
                    team2Wins["totalScore"] += int(split[4][1:-1])
                    team2Wins["listWins"].append(int(split[4][1:-1]))
                continue
            if split[1] == "shows":
                team = split[0]
                if team == team1: team1Exits["showdown"] += 1
                if team == team2: team2Exits["showdown"] += 1
                continue
            if split[1] == "FLOP":
                roundNum = 1
                continue
            if split[1] == "TURN":
                roundNum = 2
                continue
            if split[1] == "RIVER":
                roundNum = 3
                continue

    print team1Exits

    if team1 not in teamID:
        teamID[team1] = [team1Exits["round0fold"]/1000.0, team1Exits["round1fold"]/1000.0, team1Exits["round2fold"]/1000.0, team1Exits["round3fold"]/1000.0]
    else:
        listTemp = [team1Exits["round0fold"]/1000.0, team1Exits["round1fold"]/1000.0, team1Exits["round2fold"]/1000.0, team1Exits["round3fold"]/1000.0]
        teamID[team1] = [sum(x)/2 for x in zip(listTemp, teamID[team1])]
    if team2 not in teamID:
        teamID[team2] = [team2Exits["round0fold"]/1000.0, team2Exits["round1fold"]/1000.0, team2Exits["round2fold"]/1000.0, team2Exits["round3fold"]/1000.0]
    else:
        listTemp = [team2Exits["round0fold"]/1000.0, team2Exits["round1fold"]/1000.0, team2Exits["round2fold"]/1000.0, team2Exits["round3fold"]/1000.0]
        teamID[team2] = [sum(x)/2 for x in zip(listTemp, teamID[team2])]

    
    #Print useful statistics in a readable manner - add a comparison with win probabilities
    if team1 != "StraightOuttaCam" or True:
        #print
        print team1 #+ " Stats:"
        #print "Number of wins: " + str(team1Wins["wins"])
        #print "Total winning pots: " + str(team1Wins["totalScore"])
        #print "Mean win: " + str(team1Wins["totalScore"]*1.0/team1Wins["wins"])
        #print "Median win: " + str(median(team1Wins["listWins"]))
        print "Round 0 folds : " + str(team1Exits["round0fold"])
        print "Round 1 folds : " + str(team1Exits["round1fold"])
        print "Round 2 folds : " + str(team1Exits["round2fold"])
        print "Round 3 folds : " + str(team1Exits["round3fold"])
        print "Showdown exits: " + str(team1Exits["showdown"])
    if team2 != "StraightOuttaCam" or True:
        #print "----------"
        print
        print team2 #+ " Stats:"
        #print "Number of wins: " + str(team2Wins["wins"])
        #print "Total winning pots: " + str(team2Wins["totalScore"])
        #print "Mean win: " + str(team2Wins["totalScore"]*1.0/team2Wins["wins"])
        #print "Median win: " + str(median(team2Wins["listWins"]))
        print "Round 0 folds : " + str(team2Exits["round0fold"])
        print "Round 1 folds : " + str(team2Exits["round1fold"])
        print "Round 2 folds : " + str(team2Exits["round2fold"])
        print "Round 3 folds : " + str(team2Exits["round3fold"])
        print "Showdown exits: " + str(team2Exits["showdown"])

print teamID

ID = {'NeverGF': [0.0, 0.24, 0.11299999999999999, 0.068], 'ladyshark': [0.6105, 0.068, 0.03, 0.034], 'StraightOuttaCam': [0.0001802978515625, 0.0691136474609375, 0.04836376953125, 0.048177124023437504], 'Batman': [0.6555, 0.05, 0.036000000000000004, 0.03], 'LeBluff': [0.0, 0.1915, 0.11399999999999999, 0.0875], 'Battlecode': [0.5640000000000001, 0.091, 0.0455, 0.034999999999999996], '0xE29883': [0.1945, 0.186, 0.08, 0.062], 'MADbot': [0.0005, 0.1585, 0.121, 0.088]}


for team in teamID:
    currentMin = 1000000000
    bestName = "DOG"
    for identity in ID:
        euler = math.pow(abs(teamID[team][0] - ID[identity][0]), 2) + math.pow(abs(teamID[team][1] - ID[identity][1]), 2) + math.pow(abs(teamID[team][2] - ID[identity][2]), 2) + math.pow(abs(teamID[team][3] - ID[identity][3]), 2)
        #print team + ", " + identity + " " + str(euler)
        if euler < currentMin:
            currentMin = euler
            bestName = identity
    print team + " IS " + bestName






