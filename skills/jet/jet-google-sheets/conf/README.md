# 🛡️ Before you report these credentials...
If you’ve found the client_id and client_secret for our Google OAuth Desktop/CLI application in this repository, don't panic! While it looks like a security leak, it is actually an intentional and safe practice for this specific type of OAuth flow.

## Why this isn't a security risk
Unlike web applications, Desktop and Mobile applications are considered "Public Clients." They are incapable of keeping a secret because the code eventually runs on a user's machine where the "secret" could be easily extracted anyway.

Google’s security model for Desktop apps doesn't rely on the secrecy of the client_secret. Instead, security is maintained through:
* The Redirect URI: The OAuth flow is locked to http://localhost or specific custom protocol schemes. An attacker cannot use these credentials to redirect a user's login token to their own malicious server.
* The Consent Screen: The user must still explicitly grant permission. The credentials alone provide zero access to any user data or our internal Google Cloud infrastructure.

To be clear: this is a very particular, well understood and special case. We still follow strict security for other types of keys. Do NOT apply this logic to:
* Oauth Web Server Clients, These must keep their secrets hidden on the server.
* Service Account Keys, JWTs, private keys etc.

## 🤖 Why AI skills are equivalent to a Desktop App
This AI skill utilizes the OAuth 2.0 "Installed Application" flow to interact with Google Sheets. Because the skill's code is executed within a local environment (your machine, a CLI, or a local agent) rather than a protected private server, it is functionally a "Public Client." In this architecture, it is impossible to cryptographically "hide" a secret from the environment running the code. Consequently, this credentials.json acts as a public identifier for the tool, not a master key. Security is maintained by the Google Consent Screen, which requires a manual "Allow" from the user, and a loopback redirect (localhost), ensuring that data access is restricted to the person physically running the tool.

## ⚠️  Caveat: Tokens vs. Credentials
While the credentials.json in this repo is a public identifier for the app, the token.json generated in ~/.sheets-cli/ is a private session key personalized to the authenticated user. This file grants direct, password-less access to your Google Sheets and must never be shared, uploaded, or committed to version control. 

## 📋 Summary
In the world of OAuth 2.0 for native apps, the client_secret is more of a "client identifier" than a true password. Committing it here simplifies the setup for contributors without compromising our users or our platform.
Note: If you are still uneasy, feel free to check out Google’s official documentation regarding "Public Clients" and why they are handled differently.
https://developers.google.com/identity/protocols/oauth2/native-app


## 📚 References
https://developers.google.com/identity/protocols/oauth2/native-app
https://blog.sentry.security/oauth-2-0-client-credentials-misuse-in-public-apps/
https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-pkce