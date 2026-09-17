# Setting up the Joseph Smith corpus search in Claude Desktop

This connects your Claude Desktop app to our searchable index of Joseph Smith's
revelations and accounts (about 3,000 documents). Once it is installed, Claude
can search the corpus by meaning and cite the passages it finds. Setup takes
about two minutes. There is nothing else to install.

## What you need

- The **Claude Desktop app** (Mac or Windows), signed in and up to date.
- The file **`corpus-lens.mcpb`**, attached to this message.
- Your **personal access token** — a long string of letters and numbers that I
  am sending you separately. Treat it like a password: it identifies you, and
  usage is recorded per person. Please don't share or forward it.

## Install

1. Open Claude Desktop and go to **Settings → Extensions**.
   (On a Mac, Settings is under the **Claude** menu at the top of the screen.)
2. Drag **`corpus-lens.mcpb`** onto that window — or double-click the file.
3. Click **Install**. Claude will note that the extension is not from its
   official directory; that is expected, since this is our own private tool.
4. When asked, paste your token into the **Access token** box.
   Leave **Server address** exactly as it is.
5. Make sure the extension is switched **on**.

## Check that it works

Start a new chat and ask:

> Use corpus-lens to list the themes it knows.

Claude will ask permission to use the tool — allow it. You should get ten
theme names, beginning with "The Godhead." Then try:

> Use corpus-lens to find passages about baptism for the dead, and cite the source of each.

## Using it well

- **Say "use corpus-lens"** in your request. Otherwise Claude may answer from
  its general knowledge rather than searching our sources. An answer that came
  from the corpus cites documents like `1842-09-06-D&C-128 · ¶11`.
- **It searches by meaning, not keywords.** "God having a physical body" finds
  passages that say *tabernacle* or *flesh and bones*.
- **Results are in chronological order,** each with its source document and
  verse or paragraph — useful for seeing how an idea develops over time.
- **Themes:** ask Claude to "run the theme lens for The Gathering" (or any of
  the ten themes) to pull the passages most associated with that theme.
- **Editions:** when the same text exists in several editions, you get one
  result with the other editions listed beneath it. Ask Claude to "set
  distinct to false" if you want to compare the editions themselves.
- For now, results show the first 200 characters of each passage.
- There is a limit of 200 searches per person per day.

## If something goes wrong

- **"The server did not accept your access token"** — open Settings →
  Extensions → Joseph Smith Corpus Lens → Configure, and paste the token again,
  exactly as it was sent. If it still fails, ask me for a new one.
- **"Could not reach the server"** — check your internet connection and try
  again in a few minutes. If it persists, let me know.
- **Claude doesn't seem to use it** — confirm the extension is switched on in
  Settings → Extensions, start a *new* chat, and say "use corpus-lens"
  explicitly.
- Anything else: email me. Please do **not** include your token in the email.
