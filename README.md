# Asciiditor
This will be an editor for [Asciidots](www.github.com/aaronduino/asciidots), but you don't want to try it now, it is still in pre-pre-sub-alpha version.
Comme to talk on [gitter](https://gitter.im/asciidots/Lobby) ! :D 

### Install

You just need the dependancies and the repo
    
    pip install click sortedcontainers pygame
    git clone https://github.com/ddorn/Asciiditor
    
You can then try it

    python main.py FILE
    
### Configuration

Asciiditor is configurable, you just need to run. Note for windows users, you need `pyreadline` that you can install through `pip install pyreadline`.
    
    python config.py
    
The options are self explicatives, but if it's not clear, you can open an issue, 
I'll have a pleasure to explain better.
 
### Controls

Pygame beiing designed first for games, it is harder to create 
graphical interfaces like your favourites IDEs, 
however, this IDE is keyboard centered, so there are a lot of shortcuts to 
do what you want. Here is an often updated exaustive list.

- <kbd>Escape</kbd>: Quit the editor
- <kbd>F5</kbd>: Start the debugger with the current code
- <kbd>Ctrl S</kbd>: Save
- <kbd>Ctrl R</kbd>: Reset view, sixe, position when you are lost
- <kbd>Ctrl +</kbd>: Increase font size
- <kbd>Ctrl -</kbd>: Decrease font size
- <kbd>Drag left click</kbd>: Move the code around

No need to comment
- <kbd>Left</kbd>, <kbd>Right</kbd>, <kbd>Up</kbd>, <kbd>Down</kbd>: I said it will be exautive !
- <kbd>Delete</kbd>: Remove under the cursor 
- <kbd>Backspace</kbd>: Remove before the cursor
- <kbd>Click</kbd>: Set the cursor position
- <kbd>


### Comming soon (more or less)

- Syntax coloration
- autocompletion for librairies names
- Path designer
