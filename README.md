
Things this script does:

- Removes spaces from inside .epub component names (workaround for Calibre bug)
- Shortens the title from "Magical Girl Noir Quest - Book X" to "MGNQ Book X"
  (Android's bookshelf cuts the title short, and having three books called
  "Magical Girl Noir Qu..." is a pain)
- Adds thread titles to the index (ie, replaces "Thread 123", with "Thread 123: Malal IV")
- Fixes word-wrapping within XML, which breaks Android Text-To-Speech (Calibre bug)
- Tweaks Deculture's typing style a little for Android Text-To-Speech (TTS pronounces
  "No...but" as "no dot dot but" - for it to be pronounced properly, you need a space,
  eg "No... but")
- Makes the cover pages which appear on the android bookshelf consistent (Using Deculture's
  standard thread-starting image, with the book number overlaid)

