# DSR-2000-Editor
YAMAHA DSR-2000 EDITOR

THE SYNTHESIZER

The DSR-2000 is an interesting FM keyboard from 1987. A bit in the middle of the PSR and DX series.

Unlike the DX series, it was not oriented to a professional market, having a couple of speakers, a rhythm section and friendly user interface with limited synthesizing capabilities instead of a full complex editor.

However, despite the amateur PSR-ish appearance of the DSR-2000, it was more powerful than the DX series in some areas, counting with some amazing features:


* YM 2414 / OPZ, 4 Operators FM sound chip with 8 different waveforms (TX81Z, DX11 and others).
* Stereo DAC.
* Integrated BBD chorus.
* Full access to the YM edition parameters by Sysex.
* Tape / Rom pack / Sysex data bulk.
* Stereo EFX loop Inputs and Outputs.


THE EDITOR:

Basically, this app uses sysex messages to extend the DSR-2000 synthesizing capabilities to all the YM2414 parameters like the DX series do, including full access to each operator separately, waveforms, tuning, key scaling, amplitude and pitch envelopes, full LFO control, algorithm and feedback. 


The source code, Windows and mac silicon binaries can be downloaded from this folders.


The editor cannot be operated without connecting to the keyboard and loading a bank. To load the user voices bank from the keyboard, use the "Data -> Request bank" menu from the menu bar in the top of the screen, and follow the instructions from the popup window.


Since the editor still allows to modify some of the keyboard voice data parameters, some others have been disabled to avoid conflicts with the advanced edition parameters.


A set of cursor controls is implemented in the right-bottom area of the screen to access the keyboard voice data parameters. It also responds to the computer keyboard cursor keys.


Any of the 40 user presets can be edited, loaded and saved from/to disk.
The banks can also be loaded or saved from/to disk.
Please note that when a paramter is edited, the voice is automatically saved into its voice preset number.
This happens due to the characteristics of the sysex implementation in the DSR-2000.

A numeric pad is located in the bottom right area of the screen, next to the cursor controls, to change the voice number. Please note that only the user voices can be selected.


If the selected voices in the synthesizer and in the editor are different, the synthesizer voice will change to match the editor voice after editing any parameter.


The operators can be copied / pasted to make the edition easier.


The level sliders of the pitch envelope can be reset to zero clicking on them with the command key (mac) or Ctrl key (Win) pressed.


Final note: 
This development has been hard due to the lack of documentation and may be incomplete. 
Please contact to carlobandini@gmail.com if you have any documentation or information about the DSR-2000 sysex parameters. It may help to improve this editor.



