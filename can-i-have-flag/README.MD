# Can I Have Flag
## http://problems.getpwning.com:5454/

Loading the page gives you a message that you may not have a flag - we need to figure out how to get one.
There are no inputs on the page, so lets look at the request headers to see what we are working with:
```
GET / HTTP/1.1
Host: problems.getpwning.com:5454
User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-GB,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: keep-alive
Cookie: 
    __cfduid=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; 
    flask=.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx.
    xxxxxxxxxxxxxxxxxxxxxxxxxxx;
    token=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;  
    auth=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx; 
    user-auth=eyJhbGciOiJDUkMtMzIgKGxpdHRsZSBlbmRpYW4pIiwidHlwIjoiVVdUIn0%3D.dXNlck5hbWU9Um91bmQgU3F1aXJlbGwmaXNBZG1pbj1mYWxzZSZjb2xvcj0jMjE5NkYzJmZvbnRDb2xvcj0jRkZGRkZG.NTExYmU5YWY%3D
Upgrade-Insecure-Requests: 1
If-None-Match: W/"43e-YGChHZa3Zrp+sWBPE4QOv1pEnc8"
```

The problem description mentions JWT and that it might be vulnerable to a length extension attack. 
The user-auth cookie looks like a JWT token:

```
user-auth=eyJhbGciOiJDUkMtMzIgKGxpdHRsZSBlbmRpYW4pIiwidHlwIjoiVVdUIn0=.dXNlck5hbWU9Um91bmQgU3F1aXJlbGwmaXNBZG1pbj1mYWxzZSZjb2xvcj0jMjE5NkYzJmZvbnRDb2xvcj0jRkZGRkZG.NTExYmU5YWY=
```
JWTs have 3 sections - Header, Payload and Signature, separated by "." Each section is base64 encoded.
Decoding and splitting out the sections gives us the data stored in the token:

```
Header:     {"alg":"CRC-32 (little endian)","typ":"UWT"}, 
Payload:    userName=Round Squirell&isAdmin=false&color=#2196F3&fontColor=#FFFFFF, 
Signature:  511be9af 
```

The payload contains the parameter ```isAdmin=false```, we want to change it to ```isAdmin=true``` but this will make the signature invalid.

The header says this token uses a CRC-32 message signing algorithm - this is not an option for a standard JWT because it is not a secure signature. 
(The server could only use a CRC to detect a message has been tampered with if it already knows the CRC of the un-tampered message. Both the message and the CRC are provided by the client, so the server cannot know the message has been changed if the client provides a valid CRC for that message.)
We can see the type is also not JWT, it is UWT (useless web token?).

JWTs are signed as follows:
1.The header is base64urlencoded
2.The payload is base64urlencoded 
3.They are joined with a '.'
4.This string is signed with a secret key.

If the payload is simply signed with a CRC we should be able to set up a CRC generator with this state and feed additional data in to generate a valid CRC for our new message.

To generate a new valid token we can use [HashPump](https://github.com/bwall/HashPump) to append data to the existing payload and generate a new signature - this is the length extension attack.
This new payload and signature are then re-encoded into a token

I used a [python script](token.py) to generate the new token, and firefox's edit-and-resend function to make the request using the new token.
The page then loads and gives you a flag.
