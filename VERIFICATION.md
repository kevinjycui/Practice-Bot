# Application Details

## What does your application do? Please be as detailed as possible, and feel free to include links to image or video examples.
Discord to competitive programming, online judge, and problem archives integration. Links Discord users to various sites in competitive programming (AtCoder, CodeChef, Codeforces, CSES, DMOJ: Modern Online Judge, Leetcode, Szkopuł, TopCoder, and WCIPEG) based in Canada, United States of America, Russia, Japan, Finland, and Poland. Allows for fetching random problems, managing the roles/nicknames of competitive programming servers, and contest alerts. Completely open-source at https://github.com/kevinjycui/Practice-Bot

# Data Collection

## Tell us more about the data you store and process from Discord.
### What Discord data do you store?
All long-term stored data is already public. This includes online handles on competitive programming sites for users, problems solved by users, and represented country. The only piece of private data stored is API tokens for the site DMOJ: Modern Online Judge, which enables the bot to submit to problems on the user's behalf. This data is not stored in the database. Identification of users to link accounts uses a SHA-256 encrypted token to ensure proper authentication to prevent fraudulent identities.

### For what purpose(s) do you store it?
These pieces of data are necessary for the functions of the bot. DMOJ data needs to be especially stored to prevent being Cloudflared by DMOJ.

### For how long do you store it?
All already public data that is collected is stored until it is updated or deleted. DMOJ API tokens reset every time the bot is terminated or when the user becomes offline. This data is never moved anywhere outside of the programs that use it for authentication and submission.

### What is the process for users to request deletion of their data?
As all stored data is public, there is no personal data to be deleted. Under the circumstance that the user wishes to disconnect their linked accounts, commands for disconnecting are available which permanently removes selected connected accounts and associated data.

# Infrastructure

## Tell us more about your application's infrastructure and your team's security practices.
### What systems and infrastructure do you use?
The bot is written in Python and runs on the discord.py library. The database is a MySQL database, and connections between the bot and database are handled using PyMySQL. The bot in production runs on an AWS EC2 instance.

### How have you secured access to your systems and infrastructure?
All calls to the database are fully sanitized, and can only be accessed via a set amount of preset commands. There are no back doors to access the data. 

### How can users contact you with security issues?
The bot offers a suggestion command which sends the developer a message detailing the issue. The bot is also open-source on GitHub, and so users may contact the developer directly via an issue or pull request.

### Does your application utilize other third-party auth services or connections? If so, which, and why?
The bot uses the official public APIs of Codeforces and DMOJ: Modern Online Judge, trusted unofficial APIs for AtCoder, CodeChef, Leetcode, and TopCoder, and scrapes public data for CSES, Szkopuł, and WCIPEG. The bot also uses the Wikipedia Python library. All of these APIs are required for public data collection in various functions of the bot.
