
Introduction
Concepts
Topics
Information API
Overview
Footytab
Racing
Racing Models
Sports
Sports Models
Sports Result
Authentication
OAuth 2.0
OAuth 2.0 is the industry-standard protocol for for authorisation.

Endpoint
Authentication endpoint

https://api.beta.tab.com.au/oauth/token
Bearer token
A Bearer (or Access) token is an opaque string which will give you access to certain parts of the API. Bearer token must be included in HTTP Request Header in the format of Authorization: Bearer [token]

For example, if you have a bearer token of 539bdf918afc87eb376ca your request will be


GET
https://api.beta.tab.com.au/v1/tab-info-service/sports/?jurisdiction=NSW

Send

Query
[1]
Headers
[1]
Body
Path
Code Generation

jurisdiction
NSW
Key
Value
Grants
When you apply for API access, you will be given a set of credentials:

client_id, which uniquely identifies your application

client_secret, which is effectively your API password

If you have several distinct applications, you might be issued several id/secret pairs. You can check your client_id and client_secret in Settings.

You will need to use your credentials to obtain the above bearer token.

Client Credentials grant
For applications that only need non-customer data e.g. racing feeds, odds and results

If your application doesn't need place bet, you can authenticate using the client credentials grant. Given your client_id and client_secret, the API will issue a bearer token that represents your application and let you access the API.

Request format
You need to POST to https://api.beta.tab.com.au/oauth/token in x-www-form-urlencoded content type with the following fields

grant_type: client_credentials

client_id: the issued client_id

client_secret: the issued client_secret

You can try it out here, change to Body tab and make sure client_id and client_secret fields are filled with approriate values.


POST
https://api.beta.tab.com.au/oauth/token

Send

Query
Headers
[1]
Body
[3]
Path
Code Generation
Key
Value
Response format
The response is in JSON with the following fields

For example:

{
  "access_token": '000000000000000',
  "token_type": "bearer"
  "refresh_token": '111111111111111',
  "expires_in": 10800,  
}
You can then use the bearer token as shown earlier:


GET
https://api.beta.tab.com.au/v1/tab-info-service/sports?jurisdiction=NSW

Send

Query
[1]
Headers
[1]
Body
Path
Code Generation

jurisdiction
NSW
Key
Value
Note that it's up to your application to get a new token when necessary.

Password grant
For applications that act on behalf of one (or a few) specific customers, such as getting odds and placing bets automatically.

If your application needs to act on behalf of your personal TAB account, you will need to use the password grant. Please contact API support to make sure your account is configured to enable password grant.

The request is very similar to the previous flow, you need to POST to https://api.beta.tab.com.au/oauth/token in x-www-form-urlencoded content type with the following fields

grant_type: password

client_id: the issued client_id

client_secret: the issued client_secret

username: TAB account number

password: TAB account password

You can try it out here, change to Body tab and make sure client_id, client_secret, username and password fields are filled with appropriate values.


POST
https://api.beta.tab.com.au/oauth/token

Send

Query
Headers
[1]
Body
[5]
Path
Code Generation
Key
Value
The response is the same as previous flow.

The resulting bearer token then allows you to make any of the previous informational calls, as well as account-specific calls like getting your balance or full statement.

Refresh token
If your token expired (or is about to), you can request a new token without going through the entire OAuth flow.

You need to POST to https://api.beta.tab.com.au/oauth/token in x-www-form-urlencoded content type with the following fields

grant_type: refresh_token

client_id: the issued client_id

client_secret: the issued client_secret

refresh_token: the issued refresh token

You can try it out here, change to Body tab and make sure client_id, client_secret and refresh_token fields are filled with appropriate values.


POST
https://api.beta.tab.com.au/oauth/token

Send

Query
Headers
[1]
Body
[4]
Path
Code Generation
Key
Value
The response is the same as previous flow. The resulting bearer token is now issued with new expiry time.

