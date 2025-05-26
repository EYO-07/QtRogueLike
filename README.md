# QtRogueLike (in-development)
Mixed genre between Roguelike and Turn-Based Strategy using Python 3.12 and the libraries PyQt5 and noise.

Python 3.12, maybe works on older versions (not tested).
Use dependencies.bat to install the requirements (PyQt5, noise) on windows, or manually install using pip ( pip install PyQt5, pip install noise ).

Double-click on start.pyw to play or in cmd type (python start.pyw).

Currently in development, but I will appreciate if someone help testing the game ;)

## Features (They are just conceptually applied, will be improved over time)
1. Infinite Procedurally Generated Overworld.
2. No leveling system (Unlock Skills based on Days using a same character).
3. Survival Elements (Hunger).
4. Multi-level Dungeons (Entrance Can be found on Lake Biome).
5. Turn-Based Strategy Features: Buildings to Create Units, Buildings to Gather Resources (Press C on a Friendly Building).
6. Random Enemy Buildings in Overworld (Generate Certain Amount of Enemies when the player is close, Has Random Amount of Resources).
7. Can Control Multiple Characters and Create Parties (Press C in front of a Character to Add to Party, Press P or X to Release the Party).
8. Raiding Enemies Spawn (Will Search for Nearest Building).
9. The raiders's spawn quantity will progressively increase on day count capped to 50.
10. You can add any track you want on music folder, the game will randomly select and play whenever you change from one map to another.

## Gameplay

Keyboard:
1. A,W,S,D, UP, DOWN : Moves the Character.
2. W, UP : Melee Attack.
3. LEFT, RIGHT : Rotates de Camera.
4. R : Use whetstone to repair weapons.
5. E : Eat the first food in inventory.
6. C : Interact with stairs, Buildings or Friendly Characters.
7. F, CTRL, END : Special Skills which you gain surviving on day count.
8. F : To shoot with crossbows. 
9. SPACE, H : Rest. H rest 10 turns.
10. G : Get items on the floor.
11. J, I, Z, P : Open User Interfaces. J is for Journal, you can press N to take a quick note and a register your position.
12. F5 : Save the game.
13. F7 : Load the game.
14. F9 : New Game.
15. M, -, = : Music Controls.
16. Esc : Main Menu.
17. X : Skill Menu.
18. B : Build Menu. You can buy certificates on Castle Menu.
19. PageUp and PageDown : Cycle between available characters.
20. Pressing 1 or 2 to select primary and secondary weapons. 
21. Move the main window dragging it.

Mouse:
1. Move the Character clicking on cardinal adjacent tiles (The character only attacks forward).
2. Left Down and Right Down Tiles are used to rotate the character.
3. Click on Tile for Interaction, can interact with players and buildings.
4. Double-Click on friendly character to control that character.
5. Drag the main window with right mouse button.

This game was designed to be difficult and with no leveling system, the items, strategies and the skills will help defeat powerful foes. Choose your opponent carefully.
Mainly developed using A.I. assistance (Grok, ChatGPT, Copilot) and a single human brain cell.

![](poster.png)
[![Watch the video](https://img.youtube.com/vi/biM8LIhogRk/0.jpg)](https://www.youtube.com/watch?v=biM8LIhogRk&list=PLWbk3PvXtNU65GXHDNrYSaPq1jBo3L8Cq)

![](https://www.youtube.com/watch?v=)
