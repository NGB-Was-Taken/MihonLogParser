# MihonLogParser
MihonLogParser is a bot that parses through Mihon crash logs and automatically replies if it finds a known crash.

## Installation
Install dependencies
```
python3 -m pip install -r requirements.txt
```
In `main.py`
1. Replace `os.getenv("BOT_TOKEN")` with the bot's token, or add `BOT_TOKEN` to your environment variables.
2. Replace `123, 456, 789` in `roles_to_check` with the IDs of roles that should be able to execute commands.

Run `&update` (with params) once.

Run `/crash create` (with params) to add a known crash.

## Usage
Text commands
```
&help (command) (subcommand)
Shows help.

&update <major> <minor> <patch>
Changes the values of version in database. This is used to check if the user is using latest Mihon version.

&crash list
Lists all crashes in the database with their IDs.

&crash view <id>
View detailed information on a crash.

&crash delete <id>
Delete a crash.
```
Slash commands
```
/crash create <short_name>
Opens a modal for creating a known crash and reply.
short_name is required. It is used to list in "crash list" command.

Inside the modal:
- Crash message: String to look for in the log. (required)
  If `08-08 18:27:16.397  7028  7028 E app.mihon: Not starting debugger since process cannot load the jdwp agent.`
  is the line in log, the message would be `app.mihon: Not starting debugger since process cannot load the jdwp agent.`

  For responce embed:
  - Title: Title to be used in the responce embed. (required)
  - Description: Description to be used in responce embed. (required)
  - Image URL: Image url of the embed (optional)
  - Color: Color of the embed in hex (Ex: ffffff). Defaults to black (optional)


/crash edit <id> (short_name)
Opens a modal for editing crash entry with id <id>.
short_name will not be changed if not provided.
Inside the modal:
  Same as the create modal.


/crash view <id>
Same as the text command

/crash list
Same as the text command

/crash delete <id>
Same as the text command
```

