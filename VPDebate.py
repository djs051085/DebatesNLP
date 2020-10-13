# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 05:51:42 2020

@author: daniel_sandberg
"""

#*****************************************************************************
# Libraries and UDFs
#*****************************************************************************
import os
import pandas as pd
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
import textstat


def simple_word_count(myRow):
    return(len(myRow['Text'].split()))


def ts_to_seconds(timestamp,shift=0):
    fields=timestamp.split(':')
    if len(fields)==3:  #has hour/min/sec
        return(int(fields[0])*3600+int(fields[1])*60+int(fields[2])+shift)
    if len(fields)==2:  #has min/sec
        return(int(fields[0])*60+int(fields[1])+shift)
    else:               #has second
        return(int(fields[0])+shift)

def clean_crosstalk(myText):
    textList=myText.replace(']','[').split('[')
    cleanText=' '.join([x.strip() for x in textList if 'crosstalk' not in x])
    cleanText=cleanText.replace('  ',' ') #cases where double space introduced
    return(cleanText)

def str_cleaner(listText):
    cleanList=[]
    remove='-!@#$%^&*()<>.,?":{}|~\"\“\”\…'
    for mystr in listText:
        mystr=mystr.lower()
        mystr=''.join([x for x in mystr if x not in remove])
        cleanList=cleanList+[mystr]
    return(cleanList)        

def Nmaxelements(myList, myN, myUBound): 
    final_list = [] 
    
    list1=[i for i in myList if i<=myUBound]

    if myN>len(list1):
        return None
  
    for i in range(0, myN):  
        max1 = 0
          
        for j in range(len(list1)):      
            if list1[j] > max1: 
                max1 = list1[j]; 
                  
        list1.remove(max1); 
        final_list.append(max1) 
          
    return(final_list) 

def isStopword(myrow):
    if myrow.name in stopwords.words('english'):
        return(True)
    else:
        return(False)

def ngrams(textList,n):
    ngramList=[]
    for i in range(len(textList)-n+1):
        ngramList.append(textList[i:i+n])
    ngramList=[' '.join(x) for x in ngramList]
    return ngramList

#*****************************************************************************
# First we parse the transcript into machine readable format
#
# Source: https://www.rev.com/blog/transcripts/donald-trump-joe-biden-1st-presidential-debate-transcript-2020
# Source: https://www.rev.com/blog/transcripts/kamala-harris-mike-pence-2020-vice-presidential-debate-transcript
# Transcript was saved to two files (one per part) by manual screen capture
#
#*****************************************************************************

# Create Lists For Each Relevant Entry
Speaker=[]
Timestamp=[]
Text=[]

# Make the Script's Location the Working Directory
#os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.chdir('C:/Users/Daniel_Sandberg/Desktop/VPDebate_20201007\VPDebate_20201007')

# Opens the File into a List Delimited by 2 EOL Chars (Each Exchange) 
f=open("Part1.txt","r",encoding='utf-8')
p1=f.read().split('\n\n')
f.close()

# For each element in the list, 
for x in p1:
    # Get First Line - Everything before ': (' is the speaker
    xSpeaker=x.split('\n')[0].split(': (')[0].strip()
    
    # Get First Line - Everything after ': (' is the timestamp and remove extra ')' bracket
    # Convert Timer to Seconds
    xTimestamp=ts_to_seconds(
        x.split('\n')[0].split(': (')[1].replace(')',''))
    
    # Get the Second Line - Everything is speech text (CLEAN CROSSTALK)
    xText=clean_crosstalk(x.split('\n')[1])

    # Append to a List
    Speaker.append(xSpeaker)    
    Timestamp.append(xTimestamp)
    Text.append(xText)

mTime=max(Timestamp) #Gets max time of part 1

# Open Part 2
f=open("Part2.txt","r",encoding='utf-8')
p2=f.read().split('\n\n')
f.close()

# For each element in the list, 
for x in p2:
    # Get First Line - Everything before ': (' is the speaker
    xSpeaker=x.split('\n')[0].split(': (')[0].strip()
        
    # Get First Line - Everything after ': (' is the timestamp and remove extra ')' bracket
    # Convert Timer to Seconds - Add max time of part 1 
    xTimestamp=ts_to_seconds(
        x.split('\n')[0].split(': (')[1].replace(')',''),shift=mTime)

    # Get the Second Line - Everything is speech text
    xText=clean_crosstalk(x.split('\n')[1])

    # Append to a List
    Speaker.append(xSpeaker)    
    Timestamp.append(xTimestamp)
    Text.append(xText)

# Debug - Sanity Checks
print(set(Speaker)) #Gets the unique set of speakers
#print(Timestamp) #Gets all timestamps
#print(Text[0]) #Gets the first remark
#print(Text[-1]) #Gets the last remark

# To Dataframe
Debate=pd.DataFrame(
    list(zip(Speaker,Timestamp,Text)),columns=['Speaker','Timestamp','Text'])

# Debug - Drop to File
#Debate.to_csv('Debate.csv',encoding='utf-8-sig)
#print(Debate)
#print(Debate.Timestamp)


#*****************************************************************************
# Summary Stats
#*****************************************************************************

# Shorthand Arrays to Refer to Each Speaker
D=Debate['Speaker']=='Kamala Harris'
R=Debate['Speaker']=='Mike Pence'
M=Debate['Speaker']=='Susan Page'

# Words Per Section
Debate['nWords']=Debate.apply(simple_word_count,axis=1)
    
# Count Sections
print('\n\n\nTotalRows:\t',Debate.Speaker.count())
print('Democrat:\t',Debate[D].Speaker.count())
print('Republican:\t',Debate[R].Speaker.count())
print('Moderator:\t',Debate[M].Speaker.count())
print('\n\n\n')

# Cumulative Words
Debate['cumWords']=pd.concat(
    [Debate[D].nWords.cumsum()
     ,Debate[R].nWords.cumsum()
     ,Debate[M].nWords.cumsum()])


# Cumulative Unique Words
Debate['newWords']=''

DVocab=[]
DCount=[]
DBigrams=[]
DBigram_Count=[]
DTrigrams=[]
DTrigram_Count=[]
for x in Debate[D].itertuples():
    words=str_cleaner(x.Text.split()) #Gets the words, cleaned
    uWords=list(set(words))   # Gets unique words 
    newWords=[x for x in uWords if x not in DVocab] # Gets new words
    Debate.at[x.Index,'newWords']=len(newWords) # Counts new words
    DVocab=DVocab+newWords              # Appends to vocabulary
    DCount=DCount+[0]*len(newWords)     # Appends to count 
    for y in words: #For each word in the last exchange
        DCount[DVocab.index(y)]=DCount[DVocab.index(y)]+1
    
    Bigrams=ngrams(words,2)
    UBigrams=list(set(Bigrams)) # Gets unique bigrams
    newBigrams=[x for x in UBigrams if x not in DBigrams]
    DBigrams=DBigrams+newBigrams
    DBigram_Count=DBigram_Count+[0]*len(newBigrams)    
    for y in Bigrams:
        DBigram_Count[DBigrams.index(y)]=DBigram_Count[DBigrams.index(y)]+1

    Trigrams=ngrams(words,3)
    UTrigrams=list(set(Trigrams)) # Gets unique 
    newTrigrams=[x for x in UTrigrams if x not in DTrigrams]
    DTrigrams=DTrigrams+newTrigrams
    DTrigram_Count=DTrigram_Count+[0]*len(newTrigrams)    
    for y in Trigrams:
        DTrigram_Count[DTrigrams.index(y)]=DTrigram_Count[DTrigrams.index(y)]+1    

RVocab=[]
RCount=[]
RBigrams=[]
RBigram_Count=[]
RTrigrams=[]
RTrigram_Count=[]
for x in Debate[R].itertuples():
    words=str_cleaner(x.Text.split())
    uWords=list(set(str_cleaner(x.Text.split())))   # Gets unique words for this row's text (cleaned)
    newWords=[x for x in uWords if x not in RVocab] # Gets new words
    Debate.at[x.Index,'newWords']=len(newWords)
    RVocab=RVocab+newWords                          # Appends to vocabulary
    RCount=RCount+[0]*len(newWords)
    for y in words:
        RCount[RVocab.index(y)]=RCount[RVocab.index(y)]+1
          
    Bigrams=ngrams(words,2)
    UBigrams=list(set(Bigrams)) # Gets unique bigrams
    newBigrams=[x for x in UBigrams if x not in RBigrams]
    RBigrams=RBigrams+newBigrams
    RBigram_Count=RBigram_Count+[0]*len(newBigrams)    
    for y in Bigrams:
        RBigram_Count[RBigrams.index(y)]=RBigram_Count[RBigrams.index(y)]+1

    Trigrams=ngrams(words,3)
    UTrigrams=list(set(Trigrams)) # Gets unique 
    newTrigrams=[x for x in UTrigrams if x not in RTrigrams]
    RTrigrams=RTrigrams+newTrigrams
    RTrigram_Count=RTrigram_Count+[0]*len(newTrigrams)    
    for y in Trigrams:
        RTrigram_Count[RTrigrams.index(y)]=RTrigram_Count[RTrigrams.index(y)]+1    


MVocab=[]
MCount=[]
MBigrams=[]
MBigram_Count=[]
MTrigrams=[]
MTrigram_Count=[]
for x in Debate[M].itertuples():
    words=str_cleaner(x.Text.split())
    uWords=list(set(str_cleaner(x.Text.split())))   # Gets unique words for this row's text (cleaned)
    newWords=[x for x in uWords if x not in MVocab] # Gets new words
    Debate.at[x.Index,'newWords']=len(newWords)
    MVocab=MVocab+newWords                          # Appends to vocabulary
    MCount=MCount+[0]*len(newWords)
    for y in words:
        MCount[MVocab.index(y)]=MCount[MVocab.index(y)]+1
  
    Bigrams=ngrams(words,2)
    UBigrams=list(set(Bigrams)) # Gets unique bigrams
    newBigrams=[x for x in UBigrams if x not in MBigrams]
    MBigrams=MBigrams+newBigrams
    MBigram_Count=MBigram_Count+[0]*len(newBigrams)    
    for y in Bigrams:
        MBigram_Count[MBigrams.index(y)]=MBigram_Count[MBigrams.index(y)]+1

    
    Trigrams=ngrams(words,3)
    UTrigrams=list(set(Trigrams)) # Gets unique 
    newTrigrams=[x for x in UTrigrams if x not in MTrigrams]
    MTrigrams=MTrigrams+newTrigrams
    MTrigram_Count=MTrigram_Count+[0]*len(newTrigrams)    
    for y in Trigrams:
        MTrigram_Count[MTrigrams.index(y)]=MTrigram_Count[MTrigrams.index(y)]+1    


# Compile Full Vocab
Udf=pd.DataFrame({'key':DVocab,'Dem_Count':DCount}).set_index('key').join(
    pd.DataFrame({'key':RVocab,'Rep_Count':RCount}).set_index('key'),how='outer').join(
        pd.DataFrame({'key':MVocab,'MCount':MCount}).set_index('key'),how='outer')
Udf['isStopWord']=Udf.apply(isStopword,axis=1)

Bdf=pd.DataFrame({'key':DBigrams,'DBigram_Count':DBigram_Count}).set_index('key').join(
    pd.DataFrame({'key':RBigrams,'RBigram_Count':RBigram_Count}).set_index('key'),how='outer').join(
        pd.DataFrame({'key':MBigrams,'MBigram_Count':MBigram_Count}).set_index('key'),how='outer')

Tdf=pd.DataFrame({'key':DTrigrams,'DTrigram_Count':DTrigram_Count}).set_index('key').join(
    pd.DataFrame({'key':RTrigrams,'RTrigram_Count':RTrigram_Count}).set_index('key'),how='outer').join(
        pd.DataFrame({'key':MTrigrams,'MTrigram_Count':MTrigram_Count}).set_index('key'),how='outer')



# Complexity over Time
Debate['rcomplexity']=''
Debate['dcomplexity']=''


for x in Debate.itertuples():
    #-M removes Moderator and only evaluates candidates
    
    # Get the last n-many remarks by each party
    N=15
    DemIndex=Nmaxelements(Debate[D].index,N,x.Index)
    RepIndex=Nmaxelements(Debate[R].index,N,x.Index)
    
    if (DemIndex != None):
       Debate.at[x.Index,'dcomplexity']=textstat.gunning_fog(' '.join([Debate.Text.iloc[y] for y in DemIndex]))

    if (RepIndex != None):
        Debate.at[x.Index,'rcomplexity']=textstat.gunning_fog(' '.join([Debate.Text.iloc[y] for y in RepIndex]))
        

#*****************************************************************************
# Its the end
#*****************************************************************************
#Debate[R].to_csv('Debate_Rep.csv',encoding='utf-8-sig')
#Debate[D].to_csv('Debate_Dem.csv',encoding='utf-8-sig')
#Debate[M].to_csv('Debate_Mod.csv',encoding='utf-8-sig')
Debate.to_csv('Debate.csv',encoding='utf-8-sig')
Udf.to_csv('Unigrams.csv',encoding='utf-8-sig')
Bdf.to_csv('Bigrams.csv',encoding='utf-8-sig')
Tdf.to_csv('Trigrams.csv',encoding='utf-8-sig')

print('\n\nGoodbye!\n\n')
