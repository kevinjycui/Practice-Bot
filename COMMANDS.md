## Commands
### General
 - `$help` Sends you a list of my commands (obviously)
 - `$suggest <suggestion>` Sends me a suggestion
 - `$ping` Checks my ping to the Discord server
### Online Judge (DMOJ, Codeforces, AtCoder, WCIPEG integration)
 - `$login dmoj <token>` FOR DIRECT MESSAGING ONLY, logs you in using your DMOJ API token for problem submission
 - `$submit <problem-code> <language> <script>` Submits to a problem on DMOJ (requires login)
 - `$submit ^ <language> <script>` Submits to the last DMOJ problem you got using the `$random` command (requires login)
 - `$random` Gets a random problem from DMOJ, Codeforces, or AtCoder
 - `$random <online judge>` Gets a random problem from a specific online judge (DMOJ, Codeforces, or AtCoder)
 - `$random <online judge> <points>` Gets a random problem from a specific online judge (DMOJ, Codeforces, or AtCoder) with a specific number of points
 - `$random <online judge> <minimum> <maximum>` Gets a random problem from a specific online judge (DMOJ, Codeforces, or AtCoder) within a specific point range
 - `$toggleRepeat` Toggles whether or not you want problems that you have already solved when performing a `$random` command (requires at least 1 linked account)
 - `$profile <user>` See a user's linked accounts
 - `$profile` See your linked accounts
 - `$whois <name>` Searches for a user on 4 online judges (DMOJ, Codeforces, AtCoder, WCIPEG) and GitHub
 - `$notify` Lists contest notifications in a server (requires admin)
 - `$notify <channel>` Sets a channel as a contest notification channel (requires admin)
 - `$unnotify <channel>` Sets a channel to be no longer a contest notification channel (requires admin)
 ### Programming
 - `$run <language> <stdin> <script>` Runs a script in one of 72 languages! (200 calls allowed daily for everyone)
 - `$whatis <query>` Searches for something on WCIPEG Wiki or Wikipedia
 ### Fun
 - `$motivation` Sends you some (emotional) support 😊
 - `$tea <user>` Sends a user a cup of tea (a pointless point system)
 - `$tea` Checks how many cups of tea you have
 - `$cat` Gets a random cat image