#python 2.7

from hashpumpy import hashpump
from base64 import b64encode, b64decode
from urllib import quote, unquote
                                                                                                                           
token = "eyJhbGciOiJDUkMtMzIgKGxpdHRsZSBlbmRpYW4pIiwidHlwIjoiVVdUIn0%3D.dXNlck5hbWU9Um91bmQgU3F1aXJlbGwmaXNBZG1pbj1mYWxzZSjb2xvcj0jMjE5NkYzJmZvbnRDb2xvcj0jRkZGRkZG.NTExYmU5YWY%3D"
                                                                                                                           
tokenParts = unquote(token).split(".")
                                                                                                                           
decodedTokenParts = list(map(lambda part: b64decode(part), tokenParts))
                                                                                                                           
header = decodedTokenParts[0]                                                                                              
payload = decodedTokenParts[1]                                                                                             
signature = decodedTokenParts[2]                                                                                           
                                                                                                                           
#print ("header:\t\t" + header)
#print ("payload:\t" + payload)
#print ("signature:\t" + signature)
                                                                                                                           
#hashpump(hexdigest, original_data, data_to_add, key_length)
#   hexdigest is the signature
#   original_data is the payload we want to append data to
#   data_to_add is what we want to append to the payload: &isAdmin=true
#   key_length does not matter in this case (CRC32 does not use a secret key)

newSignature, newPayload = hashpump(signature, payload, "&isAdmin=true", 8)
                                                                                                                           
#print ("header:\t\t" + header)
#print ("new payload:\t" + newPayload)
#print ("new signature:\t" + newSignature)

newToken = quote(b64encode(header) + "." + b64encode(newPayload) + "." + b64encode(newSignature))
                                                                                                                           
print("New Token: \t" + newToken)
