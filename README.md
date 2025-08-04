Lightweight Python tool to sort PNG images into keyword folders based on embedded prompt/metadata. Supports copy/move semantics with configurable multi-match handling.

## Features
- Extracts prompt-like text from PNG metadata.
- Matches against user-provided keywords.
- Handles multi-keyword matches with three modes: `first`, `duplicate`, `skip`.
- GUI with thread-safe logging.
- Copy or move behavior; in `duplicate+move` mode it copies to all but the last match and moves the original to the last.

##Manual<br>
<img width="592" height="294" alt="image" src="https://github.com/user-attachments/assets/40b6efa6-d504-4620-9c3e-41d881a12a86" />

-Source Folder: directory containing PNGs with embedded prompt/metadata.
-Destination Folder: where sorted images will go.
    
-Keywords: comma-separated list (case-insensitive substring matching).

-Action: copy or move.

-If multiple matches:
    first: only the first matched keyword gets the file.
    duplicate: copy to all matches; if move is selected, original is moved to the last match and copies are placed in the others.
    skip: images matching multiple keywords are treated as no-match.

-Click Start Sorting. Logs show progress; summary dialog appears when done.



/!\The built .exe is unsigned, so Windows/antivirus may flag it or show warnings like:

"Windows protected your PC" / "Unknown publisher"
Right-click the .exe → Properties → click "Unblock" if present.
Run via "More info" → Run anyway" on the SmartScreen prompt.
