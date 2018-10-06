# IMAGE BBS v1.2b

### Copyright © 1991 New Image Software
======================================

### Manual OCRed by JOE COMMODORE.

### Modifications by IRON AXE, RASCAL, METAL MAGE, PINACOLADA, and many others.

### Updated by PINACOLADA from documentation by DR. BOB, LITTLE JOHN, and others.
=============================================================================

Handle: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_   Network
Identifier: \_\_\_\_\_\_\_\_\_\_

*Last Updated: 2018-07-14*

---

*This is just a plain text version of the OCRed sysop guide, to remind
me which sections belong where. I added commands before each section but
I think that makes it too cluttered. Better to have a command summary
appendix.*

TABLE OF CONTENTS
=================

Chapter

[Introduction](#introduction)

[Preface](#preface)

PRODUCT INFORMATION .................................iii

1  SETTING UP YOUR IMAGE BBS

Hardware considerations ...............................1

Disk drives ...........................................1

Modems ................................................1

RAM expanders .........................................2

    AutoRAMDOS ........................................

Printers ..............................................2

Interfaces ............................................2

    RS232 interfaces ..................................

Fastload cartridges ...................................2

<span id="anchor-3"></span>GETTING THINGS GOING
===============================================

<span id="anchor-4"></span>Designating drives ....................................2
===================================================================================

Copying files .........................................4

Boot disk .............................................4

<span id="anchor-5"></span>THE CONFIGURATION EDITOR
---------------------------------------------------

<span id="anchor-6"></span>How to configure a new system .........................5
===================================================================================

Device/drive assignments ..............................5

Entering BBS information ..............................7

Reloading configuration files .........................9

Saving configuration files ............................9

<span id="anchor-7"></span>MODEM SETUP
======================================

modemconfig 19.2 ..................................

   Telnet BBSes and server software ..................

tcpser 1.0rc12 ................................

tcpser4j ......................................

BBS Server ....................................

*fixme* any others...?

2  ON-LINE

BOOTING UP

    The idle screen ..................................10

    What screen masks tell you .......................

    Setting the time manually ........................

    Other command keys ...............................

The lightbar ..........................................12

    The bottom area ..................................13

<span id="anchor-8"></span>LOGGING ON
=====================================

<span id="anchor-9"></span>    RES users ........................................14
===================================================================================

    NEW users ........................................15

    The top screen after logon .......................15

    Editing system info files ........................16

    Editing sub-boards/libraries .....................17

3  GENERAL COMMANDS

   Chat request/chat mode ............................20

  Feedback ...........................................20

  Help menus .........................................20

   System information ................................20

   Last call date ....................................21

   Logging off .......................................21

   Quitting to main level ............................21

   Time and date .....................................21

  Edit parameters .................................21

EX Credit exchange .................................

PM Prompt mode .....................................21

ST Status ..........................................21

SY Sayings .........................................21

LG Activity log ....................................21

BA Board Activity Register .........................21

<span id="anchor-10"></span>TABLE OF CONTENTS
=============================================

ChapterPage

3  GENERAL COMMANDS, continued

ATC/G-ASCII-ANSI mode toggle ......................22

XP   Expert mode .....................................22

NU   New user message ................................22

ZZ   Pseudo-local mode ...............................22

Entering/changing subsystems ..........................22

Command stacking ......................................22

  4  SUB-BOARDS

Message base system ...................................23

    Moving to another sub-board ......................23

L  Lx Listing sub-boards .............................23

   Sx SA SN Scanning bulletins .......................23

A  Ax About bulletins ................................23

RA RN Reading bulletins ..............................23

    New messages .....................................24

P    Posting new bulletins ...........................24

   Kx Killing bulletins ..............................24

   Ex Editing bulletins ..............................24

\^    Frozen bulletins ................................25

    Subops ...........................................25

    Anonymous/password/non-anonymous boards ..........25

   5  UPLOAD/DOWNLOAD/EXCHANGE SUBSYSTEM

Moving to another library ............................26

PR Upload/Download protocol ...........................26

U Single file upload .................................26

UM Multi file upload ..................................26

D Single file download ...............................27

DM Multi file download ................................27

L  Lx   Listing files ................................27

Kx Ex   Killing/editing files ........................28

RxReading sequential/program files ...................28

Subops ...............................................28

VxValidating files .................................28

Copying/moving files .................................28

UX Full disk exchange libraries .....................29

Free UD/UX library ...................................29

6  ELECTRONIC MAIL SUBSYSTEM

L Listing e-mail .....................................30

\#, Ret  Reading e-mail................................30

R  Rx   Responding to a message.......................30

S Sending private e-mail..............................30

D Delete e-mail.......................................30

FRPersonal file storage...............................

Verifying e-mail......................................30

(move)  Forced e-mail.................................31

7  NEWS SUBSYSTEM

A Adding a news file..................................32

R \[Ret\] Reading news..................................32

K  Kx   Killing news files............................32

E  Ex   Editing news files............................32

L  Lx   Listing news files............................32

<span id="anchor-11"></span>8 MOVIE/PLUS/RLE/TEXT FILE LIBRARIES
================================================================

<span id="anchor-12"></span>MF  Movie file library …...............................
===================================================================================

PF Plus file library …................................

RF RLE file library ….................................

TF Text file library...................................

d.name  Making subdirectories ........................33

Chapter     Page

8MOVIE/PLUS/RLE/TEXT FILE LIBRARIES, continued

A Adding a file ........................................33

\# Entering a subdirectory or running a file ............34

K  Kx   Killing a subdirectory or file .......................34

E  Ex   Editing a subdirectory or file .......................34

  L  Lx   Listing files ........................................34

<span id="anchor-13"></span>9 BBS DATABASE SUBSYSTEM
====================================================

<span id="anchor-14"></span>BB BBS command menu .....................................35
=======================================================================================

L Listing BBSes ........................................35

A Adding a BBS .........................................35

R Removing a BBS .......................................36

E Editing BBS flags ....................................36

D Display BBS notes ....................................36

<span id="anchor-15"></span>10 VOTING BOOTH SUBSYSTEM
=====================================================

<span id="anchor-16"></span>A Add a topic ..........................................37
======================================================================================

K Kill a topic .........................................37

\# Vote/view results ....................................37

L List topics ..........................................37

<span id="anchor-17"></span>11 USER LIST SUBSYSTEM
==================================================

<span id="anchor-18"></span>    Q Quick listing ........................................38
==========================================================================================

    R Regular listing ......................................38

12 The IMAGE Text Editor(#image-text-editor)
=======================

<span id="anchor-20"></span>   Entering text ........................................39
=======================================================================================

   Editor commands ......................................39

.A / .Q Exiting the editor ...................................39

.R / .M Reading what you have typed ..........................40

   Manipulating text ....................................40

   Editor modes .........................................40

   Shaping your text ....................................40

.NStarting over ........................................41

.F / .K Searching for or replacing text ......................41

  Disk access ..........................................41

.? / .H Getting help .........................................41

   Control keys ............................................41

   Message Command Interpreter (MCI) .......................42

<span id="anchor-21"></span>13 ONLINE TERMINAL
==============================================

<span id="anchor-22"></span>Using the terminal program ...........................46
====================================================================================

The phonebook ........................................46

File operations ......................................46

<span id="anchor-23"></span>14 MAINTENANCE FUNCTIONS
====================================================

<span id="anchor-24"></span>Instant logon ...........................................47
=======================================================================================

Local maintenance commands:

R    Run a plus file .................................

ED   User editor .....................................47

CP   Online file copier ..............................48

WF   Write/edit file .................................48

ECS  Extended Command Set editor .....................

Remote Maintenance Commands:

VF   View feedback ...................................49

RS   Reserve an account ..............................50

Weeding old users ...............................50

Nightly AutoMaint ....................................

Hourly NetMaint ......................................

Miscellaneous Plus Files:

`+.access` ........................................

`+.alpha/ind` .....................................

   `+.e.modrc-config` .............................

  `+.file counter` ...............................

   `+.LB` .........................................

   `+.mail weed` ..................................

    `+.modemconfig` ................................

   `+.reconfig` ...................................50

  `+.reledit` ....................................50

   `+.text msg ed` ................................

Credit Pool Setup ............................

BASIC 2.0 utilities ..................................

`81bug.bas` ......................................

`1581diag` .....................................

`2400 setup`.......................................

`copy-all` .....................................

`dv change` ....................................

`edata edit` ...................................

`image mod maker` ..............................

`image seq reader` .............................

`rel copier` ...................................

`uconfig edit` .................................

15 Image BBS Networking ......................................

Planning a network ...................................

Network utilities ....................................

`+.NM/util` ............................................

<span id="anchor-25"></span>16 PROGRAMMING ...............................................
==========================================================================================

<span id="anchor-26"></span>Overall Description .....................................51
=======================================================================================

Modules .................................................51

Common Subroutines ......................................52

Variable Handling .......................................52

Image BBS Output Routine ................................53

POKEs And Machine Language Routines .....................54

Common Modifications ....................................

    Hidden LtK User .....................................

    Automatic CMD Device Clock Set ......................

    LtK Fast Blocks Free Read ...........................

<span id="anchor-27"></span>17  TROUBLESHOOTING Q & A ....................................55
============================================================================================

<span id="anchor-28"></span>18 VERSATILE COMMODORE EMULATOR SETTINGS .....................
==========================================================================================

<span id="anchor-29"></span>   Index .....................................................
==========================================================================================

<span id="anchor-30"></span>Command summary appendix
====================================================

*fixme*


Introduction <span id="introduction"></span>
============

In 2007, Dave “Metal Mage” Hartman and I found ourselves pondering why
there wasn't an updated version of the manual available to go along with
all the fixes and updates which had come out since Image 1.2a was
released. To get all “the good stuff” (as we call it) required reading
even *more* documentation, merging “mods” into core BBS files (sometimes
needing to start over with stock files, trumping any mods the sysop had
already made), or setting up an altar to Fred Dart.

(Believe me, I thought about it. For those of you not in the know, he
was one of the best Image programmers around; sadly, he's gone on to
that great BBS in the sky, where there surely must be an active user
base of a few billion people. At least he can party on with Ron Fick, a
Lt. Kernal guru, and Jim Butterfield... Imagine: Q-Link, with no plus
charges... oh, wait. Another Jim B.'s been there, done that. :)

Metal Mage and I decided this simply wouldn't do; it's a horrible new
sysop experience. We hacked together what we called “Image 1.2B” which
had what we considered to be the best new changes already put in. For
example: There were a few things changed by Bob “Iron Axe” Sisco with
his “Year 2000” fix which I changed back for aesthetic reasons (blue
lightbar and chat window colors don't fit in with the default grey
scheme IMHO[^1]).

Overall, we figure we've got it mostly licked.

This version of the manual includes expanded coverage, reorganized
sections, documentation of new (at the time) features which were once
available as separate add-on disks (some slated for Image 1.3):

-   a few games and BBS utilities
-   “AutoWeed,” which lets you remove callers who haven't called in a
    specified amount of time
-   the “Extended Command Set,” configurable BBS commands
-   the “TurboREL” system, faster access to message sub-boards and
    “RELedit,” the sysop-side editor
-   Image BBS networking

The "new" (released long after the original manual was
completed) Image BBS programmer's reference guide is also included in an
appendix. A lot of good information awaits you in these pages.

Please note that I've tried to introduce each new section in a sensible
way, but if you don't understand something because it hasn't been
explained yet, or it's unclear—that's a sign of bad documentation. Let
me know about it; I'll have myself flogged (let me start the noodles
cooking).

Having previous experience with the software, I've tried not
to fall into the trap of “it's obvious to *me*, not necessarily everyone
else.” And while I do try to define possibly unfamiliar terms, you won't
find a glossary with “upload” and “download” in it, at least not here.
Already being familiar with BBS basics (perhaps having called an Image
BBS as a user before?) is extremely helpful. However, don't let my
pseudo-gruffness stop you from contacting me if you run into something
you don't understand!

99% of the following work is either the New Image crew, Joe Commodore,
or someone else. I just ran it all through a blender, baked until golden
brown, *et voila*! It *must* be true: Anyone can cook.

Many thanks go to Larry “Joe Commodore” Anderson for OCR'ing the 1.0
manual plus the updates! Also thanks to Rascal, Iron Axe, Metal Mage,
Fred Kreuger, and anyone else I forgot.

I just want this to be the best, most comprehensive manual available,
given all the great fixes that have come out since Image 1.0
came out. Who knows, maybe you've got the next hot modification or
suggestion—or an answer to some burning Image BBS question which kept me
up nights.

## Surgeon General's Warning
-------------------------

By no means must you read through this documentation in one sitting, or
a day, or a week. Take it in bite-sized (byte-sized?) chunks; I sure
remember the intimidation I felt when I saw the original manual... Just
take a deep breath, have some milk and cookies, and come back to it
later. Scribble stuff in the margins. Tune in, turn on, boot up!

<span id="anchor-40"></span>
## Blatant Begging (On Hands and Knees Even)
-----------------------------------------

Also, I would like to collect any information about Image BBS you or
your friends and colleagues have. Back in the 1990s there were
*hundreds* of Image sysops-—they can't all have died *yet*. :) Any
plus-files, programming information, “Reflections” or NISSA (New Image
Sysop Support Association) e-zines you've got—in short, *anything*
Image-related-please forward it to me.

My goal is to revive Image BBS and its network, to re-kindle the
feelings of anticipation when there was a new plus file or mod
to download.

> As of 2014, Larry "X-Tec" Hedman is the NISSA and network
> administration guy. We have 13 notes as of July 2018.

<span id="anchor-44"></span>Anyway, drop me a line—I want to hear from
you! plzkthx.

PinaDox (^tm^ & pat. pend.—I've never patted a pend. before but I'm
willing to try anything): The only user-friendly documentation with a
built-in sense of humor. Well, okay, I amuse myself, and that's what's
important.

<span id="anchor-45"></span>Text Styling Notes
==============================================

This version of the manual has some enhanced typographical features.
Firstly, by and large a proportional font is used. I have
nothing against monospaced text—after all, it's what a BBS is made
of—but in the long run it really makes my eyes bug out looking at pages
upon pages of it.

*Text output by the BBS, and filenames, are italicized.*

`Keyboard keys (like Return) and user input are monospaced.`

> Additional sections, information, or changes from the original
> manual are indented.

There are the beginnings of cross-references to where sections are now.
If you see a missing cross-reference, please let me know.

-Ryan “Pinacolada” Sherwood\

<span id="anchor-46"></span>
Larry Anderson’s Introduction
=============================

Dear Reader:

Here it is, the much-needed documentation of Image 1.2a BBS.  This is an
OCR of the original documentation, which included the Image 1.0 manual
and addendum sheets for Image 1.1 and 1.2.  If you are setting up 1.2,
make sure to read the 1.2 addendum as well as the 1.0 manual.

Notes:

If you are setting up Image, use the 1.0 diskette, and copy over the 1.2
files on to a copy of the 1.0 diskette (overwriting the outdated 1.0
files).

> Even better: Save yourself the hassle—use Image 1.2b!

There are special notes if you are using a Supra 2400 baud modem as well
as using a CMD or Lt. Kernal hard drive.

The modification diskettes for TurboRELs and BBS-to-BBS networking
contain their own install/usage documentation on the disk image. (Note:
Using TurboREL message bases on a 1581 drive may be problematic; e-mail
me if you need more info on it.)

> This is probably because of the "secondary address \#1" bug.  I have
> included the BASIC program 81bug.bas to demonstrate it, if you're
> interested.  I need to get in touch with Larry to see whether this is in
> fact the cause.

In its' time, Image BBS was one of the top-of-the line Commodore 64
BBSes, even compared to PC counterparts of the day.  Image held its own
in features and adaptability.

> The BBS numbers in the following
> documentation are all long gone, please do not try calling them.

Enjoy!\
Larry Anderson\
Sysop - Silicon Realms BBS\
[larry@portcommodore.com](mailto:larry@portcommodore.com)
========================================================

<span id="anchor-50"></span><span id="anchor-51"></span><span id="anchor-50"></span>Package intro letter
========================================================================================================

<span id="anchor-52"></span>New Image Software\
P.O.  Box 525\
Salem, UT 84653\
801-423-1966
===============================================

Dear Customer and Friend:

We thank you very much for ordering IMAGE BBS v1.0!!  We think that you
will be very happy with your purchase, and intend to fully support our
customers in any way that we can.  If you need any help whatsoever in
setting up your BBS or maintaining it, please feel free to contact us by
mail, phone, or BBS, and we will do what we can.

This version was "supposed" to be released long ago, but due to problems
in relocating our offices and other things, it is late.  (Ever have
5,000 screaming sysops on YOUR phone line?!?) We apologize immensely for
this, but feel that the quality of the program will make you forget
about this very soon! Read the manual through and see the options that
you have with this BBS program!

Please also notice that we have added a few things that are not
documented in the manual.  The ist function in the subsystems now shows
to the user if the sub-board/library is a "special" one, highlighting
the library in color, and also showing an abbreviation at the beginning:

"N-An" means a non-anonymous sub-board.

"Anon" means anonymous sub-board.

"Pass" means password-protected sub-board, and

"Free" means a free UD/UX library.

<span id="anchor-53"></span>See the manual for more information on
these.

Also, please note that the support BBS and voice numbers for the
northern (Michigan) region are no longer valid.  The new BBS support
line for the north (Lyon's Den BBS) is 313-453-2576.

24 hrs—300-1200 baud.

<span id="anchor-54"></span>The new main voice support line will be
located in Utah, as listed in the manual, 801-423-1966.

The new southern (Florida) support lines are: voice: 904-756-1206—Ron
Fitch, and the Tec-Net BBS is 904-756-2700.

Night Flight BBS listed in the manual is no longer associated with us;
the rest of the numbers are all still valid.

<span id="anchor-55"></span>Add these variables to the list on page 53:
`BF`, `CH$`, `PO$`, `KP%`, `MM`.

Our plans for the future:

There is no programmer's manual for the software available yet, but we
DO plan to write one in the near future.  You will be seeing many
modules available for IMAGE soon, both translated from old popular
winners, and brand new!  You will also see utilities for running your
BBS, both in module form, and runnable in BASIC to make things easier
for you.  We plan to write a terminal program that will interact with
IMAGE to allow full sound, high-res graphics and sprites for the user,
and will have the same module routines as the BBS does.  This will allow
you to write a module (plus file) for BOTH the term and the BBS that
will interact.  A 128 version of IMAGE is also planned.  As is our
policy, NO release announcements will be made until the new products are
ready.

As always, we welcome comments, suggestions, and criticism at any time,
so please let us know what you think!  Looking forward to a long, happy,
and mutually satisfying relationship with you!  Keep in touch!

Don Gladden\
New Image Software

<span id="anchor-56"></span><span id="anchor-57"></span><span id="anchor-56"></span>Addenda for Image 1.2a, page 1
==================================================================================================================

<span id="anchor-58"></span>Congratulations on your purchase of IMAGE BBS V1.2a.
================================================================================

We believe that you have purchased the finest BBS program available
today for the Commodore 64.  The program is continually being updated
and refined and some of the latest updates have not yet made it into the
manual.  For that reason we are including this short addendum.  Version
1.2a differs only slightly from 1.2.  It includes the “CMD Mods,” or the
changes necessary to allow the use of partitions from 1 to 255 on that
particular drive.  It can still be used on any other system, including
the Lt. Kernal.  Caution should be taken however, as it is now possible
to address LU 10, the DOS LU.  All of the “mods” are installed so there
is no need to download any “CMD Mod” packages.

Some of the features from 1.2 that are not clear in the manual include
the selection of the proper modem file.  The manual states, incorrectly,
that you should choose a modem file that matches your modem and rename
it to `+.modem`.  That has been changed.  There is now a `+.modem` file
on the disk that is universal.  Be SURE to use that file, and use the
`modemconfig` file to select your proper modem type.

*NOTE:* If you are using ANY 2400 baud modem, you must run the `2400
setup` file first *before booting the BBS*.

The `u.alpha` file has been replaced by `u.index` that is maintained and
manipulated by a file called `+.alpha/ind`.  Should your index become
corrupted, one common complaint is that users can sign on with their ID
number but not their handle.  If that should occur, run the
`+.alpha/ind` from the main prompt and choose the options LOAD, CLEAR,
MAKE and SAVE in that order.  It is very important that you follow those
steps; saving is required, since the program will not save for you.

The “macros” are installed in 1.2.  There are “mods” out that call for
lines to be added to `setup` and `im` but they are already in, all you
need is the `+.ME` (macro editor) that is available on the PlusFile disk
\#4.  After you have the macro editor, you can define your macros and
then turn them on by putting the check mark on the right side of
*Exp* on the second page of the lightbar (press `F8`).

The support numbers in the manual are wrong.  The one voice support line
is 801-423-2209.  The BBS numbers are:

```
Port Commodore  801-423-2734
Lyon's Den East 313-453-2576
GearJammer's II 215-487-0463
```

<span id="anchor-59"></span>We hope you enjoy your IMAGE and if you need help don't hesitate to call.
=====================================================================================================

<span id="anchor-60"></span>—NEW IMAGE SOFTWARE
===============================================

<span id="anchor-61"></span><span id="anchor-62"></span><span id="anchor-61"></span>Addenda for Image 1.2a, page 2
==================================================================================================================

Here are some changes that have been made since the manual was printed.
Please note them carefully.

<span id="anchor-63"></span>Pg 1  DISK DRIVES
=============================================

Since the release of the CMD hard drive, IMAGE was updated to version
1.2A, which includes the "CMD Mods."  IMAGE now has the ability to
address partitions 1 through 254.

<span id="anchor-64"></span>Pg 4  DESIGNATING DRIVES
====================================================

IMAGE 1.2 added some new files called *scn.*xx** (where *xx* is *t1 t2
t3 t4, c1 c2 c3 c4* files.  This consists of eight "screen" files.
These files must be placed on the plus file drive for proper operation.
*They are text and color, respectively, of the screen masks displayed at
system idle, or other areas on the BBS.*

<span id="anchor-65"></span>Pg 5  COPYING FILES
===============================================

In this section you are told to choose the modem file that matches your
modem and rename it to `+.modem`.  That is no longer necessary.  There
is now only *one* modem file for all 1200 and 2400 baud modems, and it
is `+.modem`.  After you have completed the configuration of your board,
run the `modemconfig` file and select the modem type you are using.  It
will then write the parameters to the etcetera disk.  Any time you
change modems it is only necessary to run the `modemconfig` or
`+.modemconfig` to re-select your modem type.

NOTE: If you are using ANY 2400 baud modem, it is necessary to run the
`2400 setup` file which sets the modem up to respond to IMAGE.  With the
Aprotek "MiniModem C24" it is necessary to run `2400 setup` any time the
computer is turned off for more than a few seconds.

<span id="anchor-66"></span>Pg 16 THE LIGHTBAR
==============================================

There are now two pages to the lightbar.  The first page remains the
same, the second page has only three functions that are used
immediately.

The first is *Asc* which is:

(L)ASCII on/off

(R)linefeeds on/off

The second is *Ans* which is:

(L)ANSI on/off

(R)IBM Graphics on/off.

The third is *Exp* which is:

(L)expert mode on/off

(R)macros on/off (note that they are already installed)

In addition, the Turbo-RELs use *Fn5* for:

(L)credit when file is uploaded or when validated

(R)log off after file transfer is complete

<span id="anchor-67"></span>The CMD mods (1.2a) also introduced the right side of *Fn1* which turns MCI off when checked.
=============================================================================================================================

<span id="anchor-68"></span>Pg 29  COMMANDS
===========================================

There is no longer a `BC` (baud change) option.

The heck there isn't!  I put it back for historical preservation, even
though it's unlikely to do anything useful!   Yay me.

<span id="anchor-69"></span>Pg 55 THE IMAGE EDITOR
==================================================

Some commands have been changed and some print modes have been added or
changed.  Check the menu in the editor for current commands/modes.

<span id="anchor-70"></span>
Preface
=======

We feel that the program you have just received, IMAGE BBS version 1.2,
is the most versatile and elaborate BBS program for the Commodore 64
computer available today!  It is the result of over five years of work
and many hours of programming time, has taken ideas from modem users and
BBS sysops all over the world for its design, and offers many hours of
pleasure for both BBS callers and sysops.  If you are a programmer, or
even a novice programmer, IMAGE BBS is designed to be easy to modify to
suit your own tastes, and even to add modules to do any type of function
on the BBS that you may wish to have!  With some practice, and knowledge
of IMAGE programming techniques, virtually anything is possible to add
to your BBS.  We have included some basic information on technique to
get you started, and plan on releasing a more comprehensive programmer's
manual in the near future.

Thanks go out to all who have supported us in the past with our
programs, and for all the suggestions and ideas that have been shared
with us.  If you need to contact us for anything at all, please feel
free to at any of the voice or BBS numbers supplied on page v of this
preface.

<span id="anchor-74"></span>Special Thanks To:
----------------------------------------------

Peggy:

> For being an understanding wife while this program was being
> developed, taking over the business end of things at a time when it
> was needed, and helping to make decisions, some of which were really
> tough.  I don't believe this program would be possible without her.

Jamie, Christy, Billy, and Kim:

> For their support, patience and understanding in giving Dad (and
> sometimes Mom) up for all the extended programming and business
> sessions.

Ray Kelm (PROFESSOR):

For being the sharpest ML whiz-kid in the world, and all the quality
work.

Fred Dart (THE CHIEF):

> For the EXTENSIVE beta-testing and bug reports.  (Not sure why I'm
> THANKING him for bugs, but...)  Also, for his enormous phone bills in
> getting this thing done as soon as possible.  And for many other
> things too numerous to detail.

Jay Levitt:

> For representing us on QuantumLink for so long, and the work he has
> helped with on the program, especially the e-mail routines.

*Bob DiLorenzo (BLINKY):*

> For beta-testing, the vacation and tour of Opryland in Tennessee when
> I needed that break so bad, and for being such a good friend.

Jim Flinn (MUZAK MAN):

> For designing the awesome title screen and beta testing.

Mark Verellen (KING TRENT):

> For bringing over the Cokes when I was broke, and being official IEEE
> beta tester.

Mike Coley (THE HAPPY HACKER):

> For the voting booth, and so many great ideas! (Where are you, Mike,
> haven't heard from you!)

Julie Rhodes (BLUE ADEPT):

> For the new BBS List program, and all her support.

John Moore (LITTLE JOHN):

> For joining up with us, and starting work on the 128 version of
> IMAGE.  Also for the graffiti routines in the logon.

Rich Matteo (SHADOW WARRIOR):

> For the use of his modifications for the multi U/D and full disk
> exchange routines, to make it so much easier for us to add.

Tony DeLiberato (ULTRA LORD):

> For his help on the production of this manual and advertising layouts.

John and Paul at QuantumLink:

> For their help and support on Q.

Fiscal, Xetec, Trans-Comm, InConTrol, and the many other companies who
were so cooperative in helping us develop the program to allow their
products to be used.

<span id="anchor-75"></span>And finally, to YOU, for trying IMAGE BBS
out!  We're sure you won't be sorry you did!

<span id="anchor-76"></span>Don Gladden\
New Image Software
========================================

<span id="anchor-77"></span><span id="anchor-78"></span><span id="anchor-77"></span><span id="anchor-79"></span><span id="anchor-77"></span><span id="anchor-78"></span><span id="anchor-77"></span><span id="anchor-80"></span><span id="anchor-77"></span><span id="anchor-78"></span><span id="anchor-77"></span><span id="anchor-79"></span><span id="anchor-77"></span><span id="anchor-78"></span><span id="anchor-77"></span>Product Information
=======================================================================================================================================================================================================================================================================================================================================================================================================================================================

This section contains all warranty, program usage, and support
information.<span id="anchor-81"></span>This section contains all
warranty, program usage, and support information.

<span id="anchor-82"></span><span id="anchor-83"></span><span id="anchor-82"></span><span id="anchor-84"></span><span id="anchor-82"></span><span id="anchor-83"></span><span id="anchor-82"></span><span id="anchor-85"></span><span id="anchor-82"></span><span id="anchor-83"></span><span id="anchor-82"></span><span id="anchor-84"></span><span id="anchor-82"></span><span id="anchor-83"></span><span id="anchor-82"></span>Usage Agreement
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

You have the non-exclusive right to use the enclosed program.  Copying
the program with the intention of distributing it to others, whether or
not for personal gain is illegal and not in accordance with this
agreement.  Modifications of this program may be made for personal use,
and to share with other REGISTERED owners; however, the modifications
should be shared as modules.  Do not distribute the program in its
entirety.

<span id="anchor-86"></span><span id="anchor-87"></span><span id="anchor-86"></span><span id="anchor-88"></span><span id="anchor-86"></span><span id="anchor-87"></span><span id="anchor-86"></span><span id="anchor-89"></span><span id="anchor-86"></span><span id="anchor-87"></span><span id="anchor-86"></span><span id="anchor-88"></span><span id="anchor-86"></span><span id="anchor-87"></span><span id="anchor-86"></span>Back-up and Transfer
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Backups may be made of this program; however, you must include the
copyright notice and serial number on any back-up copies.  Transfer of
registration may be done by sending signed written notice from the
original purchaser, releasing his registration rights.  Contact New
Image Software for further instructions regarding transfer.

<span id="anchor-90"></span><span id="anchor-91"></span><span id="anchor-90"></span><span id="anchor-92"></span><span id="anchor-90"></span><span id="anchor-91"></span><span id="anchor-90"></span>Copyright
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

This program and documentation manual are copyrighted under the laws of
the United States *and Canadian* government*s*.  You may not copy the
program for distribution purposes at any time, whether for personal gain
or not.  You may NOT remove the copyright notice or serial number at any
time.

<span id="anchor-93"></span><span id="anchor-94"></span><span id="anchor-93"></span><span id="anchor-95"></span><span id="anchor-93"></span><span id="anchor-94"></span><span id="anchor-93"></span>Limited Warranty On Disk
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

New Image Software warrants the DISK on which the program is furnished
to be free from defects in materials and workmanship under normal use
for a period of 90 days from the date of purchase on your receipt.  To
obtain service or replacement, you must deliver the disk prepaid to New
Image Software.  The responsibility of New Image software is limited to
repair or replacement of the original disk and/or documentation manual.
The program and the manual ("software") are provided without warranty of
any kind, either express or implied, including, but not limited to, the
implied warranties of merchantability and fitness for a particular
purpose.  New Image Software does not warrant, guarantee, or make any
representations regarding the use of, or the results of use of, the
program in terms of quality, correctness, accuracy, reliability,
currentness, or otherwise, and you rely on the program and results
solely at your own risk.  New Image Software also does not warrant that
the program or manual will meet your requirements, or that the program
will be uninterrupted or error-free.

EXCEPT TO THE EXTENT PROHIBITED BY APPLICABLE LAW, ANY IMPLIED WARRANTY
OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE ON THE DISK IS
LIMITED TO THE DURATION OF THIS LIMITED WARRANTY.

<span id="anchor-96"></span><span id="anchor-97"></span><span id="anchor-96"></span><span id="anchor-98"></span><span id="anchor-96"></span><span id="anchor-97"></span><span id="anchor-96"></span><span id="anchor-99"></span><span id="anchor-96"></span><span id="anchor-97"></span><span id="anchor-96"></span><span id="anchor-98"></span><span id="anchor-96"></span><span id="anchor-97"></span><span id="anchor-96"></span>Limitations of Remedies
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

In no event will New Image Software be liable to you for any damage in
excess of your license fee paid, including, without limitations, any
lost profits, business goodwill or other special incidental or
consequential damages arising out of the use or inability to use the
program, or for any claim made by any other party, even if New Image
Software or the dealer had been advised of the possibility of such
claims or damages.

This warranty gives you specific legal rights and you may also have
other rights which vary from state to state.

<span id="anchor-100"></span><span id="anchor-101"></span><span id="anchor-100"></span><span id="anchor-102"></span><span id="anchor-100"></span><span id="anchor-101"></span><span id="anchor-100"></span>Update and Customer Support Policy
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

In order to be able to obtain any customer support or updates of the
program, you *must* complete and return the enclosed registration card
to New Image Software.  If this registration card has not been received
by New Image Software, or New Image Software is aware of breach of any
part of this agreement by you, New Image Software is under no obligation
to make available to you any customer support or updates of the program
even though you have made payment of the applicable update fee.

<span id="anchor-103"></span><span id="anchor-104"></span><span id="anchor-103"></span><span id="anchor-105"></span><span id="anchor-103"></span><span id="anchor-104"></span><span id="anchor-103"></span>Acknowledgment
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

You acknowledge that you have read this agreement, understand it, and
agree to be bound by  its terms and provisions by filling out and
returning the enclosed registration card.  You also agree that this
agreement is the complete and exclusive statement or agreement between
the parties and supersedes all proposals or prior agreements, verbal or
written, and any other communications between the parties relating to
the subject matter of this agreement.

Should you have any questions concerning this agreement, please contact
*in writing*:

<span id="anchor-106"></span>New Image Software\
Customer Sales and Support\
P.O. Box 525, Salem, UT 84653
================================================

> *Dead address, of course.*

<span id="anchor-107"></span><span id="anchor-108"></span><span id="anchor-107"></span><span id="anchor-109"></span><span id="anchor-107"></span><span id="anchor-108"></span><span id="anchor-107"></span><span id="anchor-110"></span><span id="anchor-107"></span><span id="anchor-108"></span><span id="anchor-107"></span><span id="anchor-109"></span><span id="anchor-107"></span><span id="anchor-108"></span><span id="anchor-107"></span>User Support
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

THANK YOU VERY MUCH FOR PURCHASING IMAGE BBS!  This manual is a very
detailed description of the features and capabilities of the program.
However, if you have any questions left unanswered, or if you discover
any problem with any part of the program, please feel free to contact us
at any of the following BBS or voice support lines.

LYON'S DEN BBS (Central Region: Michigan)\
BBS: 313-453-2576  24 hrs.  300-2400 baud.\
System Operator: Ray Kelm (Professor)

PORT COMMODORE BBS (Western Region: Utah)\
BBS: 801-423-2734  24 hrs.  300-2400 baud.\
9:00AM to 5:00PM MST\
Voice Tech line: 801-423-1966\
System Operator: Fred Dart (The Chief)

For support, call any of the support boards listed or any of the tech
lines listed during the hours listed.  These locations are set up for
your convenience, you may call any of them but you might want to call
the one nearest to you; they are located in the states shown.

The bulletin boards listed all have many users that are IMAGE BBS
owners; they love to share modifications and ideas!  You can benefit
greatly by being a member of any of these BBSes.

Additional support can be found on QuantumLink.  Each of the above
listed support personnel are available on QLink as: IMAGE Don, IMAGE
Fred, and IMAGE Jay and will make every attempt to assist you in any
way.

**Note:** Until further notice, this manual covers all\
current versions of Image BBS: 1.0, 1.1 and 1.2.

****Update 7/2014: ****There is a Facebook group and the beginnings of a
support web site, “Pinacolada's Projects,” located at
&lt;**[**https://sites.google.com/site/pinacoladasprojects/**](https://sites.google.com/site/pinacoladasprojects/)**&gt;.\
\
Also, stop by Jeff Ledger's "Commodore TelBBS forum," where there is
some archived information about Qlink and telnet BBSes:
&lt;**[**http://jledger.proboards19.com/**](http://jledger.proboards19.com/jledger.proboards.com)[**jledger.proboards.com**](http://jledger.proboards19.com/jledger.proboards.com)**&gt;**

Setting Up Your Image BBS
=========================

Setting up should be very simple.  We suggest you read this chapter
carefully, following the instructions step by step.  The configuration
editor also has built-in documentation to help you out.

<span id="anchor-114"></span><span id="anchor-115"></span><span id="anchor-114"></span><span id="anchor-116"></span><span id="anchor-114"></span><span id="anchor-115"></span><span id="anchor-114"></span><span id="anchor-117"></span><span id="anchor-114"></span><span id="anchor-115"></span><span id="anchor-114"></span><span id="anchor-116"></span><span id="anchor-114"></span><span id="anchor-115"></span><span id="anchor-114"></span>Hardware Considerations
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

IMAGE BBS has been tested with many different types of peripherals, and
usually has no problem running with any Commodore compatible equipment.
If you have any problems, please contact us at one of our support
centers listed in this manual for help, and we will do all we can to
help you to make IMAGE BBS work with your system.  Some modems and
drives deviate from the Commodore standard enough to cause some
problems, but this is usually fixable with some patches into the
program(s).  Some of the peripherals tested with IMAGE BBS and found to
work well are:

### <span id="anchor-118"></span><span id="anchor-119"></span><span id="anchor-118"></span><span id="anchor-120"></span><span id="anchor-118"></span><span id="anchor-119"></span><span id="anchor-118"></span><span id="anchor-121"></span><span id="anchor-118"></span><span id="anchor-119"></span><span id="anchor-118"></span><span id="anchor-120"></span><span id="anchor-118"></span><span id="anchor-119"></span><span id="anchor-118"></span>Disk Drives

-   All Commodore drives (1541, 1571, 1581, and IEEE drives)
-   Xetec Lt. Kernal hard drives
-   Creative Micro Designs hard drives
-   ICT Datachief and Minichief hard drives (see notes below)

### <span id="anchor-122"></span><span id="anchor-123"></span><span id="anchor-122"></span><span id="anchor-124"></span><span id="anchor-122"></span><span id="anchor-123"></span><span id="anchor-122"></span>Lt. Kernal Hard Drives

IMAGE was completely developed using a Lt. Kernal drive, using LUs 0 to
9, so is completely compatible with this drive in all respects.

### <span id="anchor-125"></span><span id="anchor-126"></span><span id="anchor-125"></span><span id="anchor-127"></span><span id="anchor-125"></span><span id="anchor-126"></span><span id="anchor-125"></span><span id="anchor-128"></span><span id="anchor-125"></span><span id="anchor-126"></span><span id="anchor-125"></span><span id="anchor-127"></span><span id="anchor-125"></span><span id="anchor-126"></span><span id="anchor-125"></span>CMD Hard Drives

They work.  CMD mods.

### <span id="anchor-129"></span><span id="anchor-130"></span><span id="anchor-129"></span><span id="anchor-131"></span><span id="anchor-129"></span><span id="anchor-130"></span><span id="anchor-129"></span><span id="anchor-132"></span><span id="anchor-129"></span><span id="anchor-130"></span><span id="anchor-129"></span><span id="anchor-131"></span><span id="anchor-129"></span><span id="anchor-130"></span><span id="anchor-129"></span>ICT Hard Drives

This drive has a problem in chain mode that will not allow more than one
file to be open at a time.  IMAGE does use more than one file at once in
some areas, so we suggest not using the ICT drive for the E-mail or
Etcetera disk, or for sub-boards.  Any other system function should work
fine with the ICT drive.

### <span id="anchor-133"></span><span id="anchor-134"></span><span id="anchor-133"></span><span id="anchor-135"></span><span id="anchor-133"></span><span id="anchor-134"></span><span id="anchor-133"></span><span id="anchor-136"></span><span id="anchor-133"></span><span id="anchor-134"></span><span id="anchor-133"></span><span id="anchor-135"></span><span id="anchor-133"></span><span id="anchor-134"></span><span id="anchor-133"></span>Modems

  ------------------------ -----------------------------------------
  ------------------------ -----------------------------------------

Table : Supported modems

<span id="anchor-137"></span>See the "Questions & Answers" section, page
in the programming chapter for more information on setting the BBS up
for your particular modem or telnet bridge.  (NOTE: The modem routines
in IMAGE BBS are contained in individual modules, so if a modem is not
supported, it is very likely that a module will be written for it that
will allow its use soon.)

### <span id="anchor-138"></span><span id="anchor-139"></span><span id="anchor-138"></span><span id="anchor-140"></span><span id="anchor-138"></span><span id="anchor-139"></span><span id="anchor-138"></span><span id="anchor-141"></span><span id="anchor-138"></span><span id="anchor-139"></span><span id="anchor-138"></span><span id="anchor-140"></span><span id="anchor-138"></span><span id="anchor-139"></span><span id="anchor-138"></span>RAM Expansion Units

IMAGE BBS has been tested successfully on systems using REUs in
conjunction with other peripherals.  Version 071487 of Commodore's
RAMDOS is provided.  It is set to define your RAMdisk as device 7, which
is how it is supported by Image BBS.

  ----- -----------------------------------------------------------------------------------
  ----- -----------------------------------------------------------------------------------

<span id="anchor-142"></span>Table : RAMDOS files

### <span id="anchor-143"></span><span id="anchor-144"></span><span id="anchor-143"></span>Printers

Most Commodore compatible printers should work with IMAGE BBS.  Standard
Commodore routines are used by the program; using logical file \#4,
device \#4, with a secondary address of 7 to allow for upper- and
lower-case.

### <span id="anchor-145"></span><span id="anchor-146"></span><span id="anchor-145"></span><span id="anchor-147"></span><span id="anchor-145"></span><span id="anchor-146"></span><span id="anchor-145"></span><span id="anchor-148"></span><span id="anchor-145"></span><span id="anchor-146"></span><span id="anchor-145"></span><span id="anchor-147"></span><span id="anchor-145"></span><span id="anchor-146"></span><span id="anchor-145"></span>Other Interfaces

Some IEEE or printer interfaces could feasibly cause some problems due
to memory conflicts, and would need some customization of the program to
allow use.  Two IEEE interfaces commonly used and tested with IMAGE BBS
are the "IEEE Flash!" by Skyles Electric Works, and the "BusCard II" by
Batteries Included, both of which perform well.

### <span id="anchor-149"></span><span id="anchor-150"></span><span id="anchor-149"></span><span id="anchor-151"></span><span id="anchor-149"></span><span id="anchor-150"></span><span id="anchor-149"></span><span id="anchor-152"></span><span id="anchor-149"></span><span id="anchor-150"></span><span id="anchor-149"></span><span id="anchor-151"></span><span id="anchor-149"></span><span id="anchor-150"></span><span id="anchor-149"></span>RS232 (EIA232) Interfaces

There are two files: *ml.rs232/user* and *ml.rs232/swift*—depending on
the type of modem or telnet bridge you'll be using, rename one to
*ml.rs232* in order to achieve the proper setup.

### <span id="anchor-153"></span><span id="anchor-154"></span><span id="anchor-153"></span>Fastload Cartridges

At the present time, we recommend that no fastloader cartridges be used
with IMAGE BBS, they may only cause problems.

****Please give any information about other fastload solutions you have
success with using. 1541 fastload routines are present in the
as-yet-unreleased Image 2.0!**<span id="anchor-155"></span>****Please
give any information about other fastload solutions you have success
with using. 1541 fastload routines are present in the as-yet-unreleased
Image 2.0!**

### <span id="anchor-156"></span><span id="anchor-157"></span><span id="anchor-156"></span>Creative Micro Designs SuperCPU

**There are ****patches to make the BBS run at 20 mHz. During file
transfers, the BBS must be slowed down to 1 mHz with a POKE to the
SuperCPU speed register.**

<span id="anchor-158"></span><span id="anchor-159"></span><span id="anchor-158"></span><span id="anchor-160"></span><span id="anchor-158"></span><span id="anchor-159"></span><span id="anchor-158"></span><span id="anchor-161"></span><span id="anchor-158"></span><span id="anchor-159"></span><span id="anchor-158"></span><span id="anchor-160"></span><span id="anchor-158"></span><span id="anchor-159"></span><span id="anchor-158"></span>Getting Things Going
=======================================================================================================================================================================================================================================================================================================================================================================================================================================================================

Now that you are ready to set up IMAGE BBS, we recommend you first back
up your original disk (both sides if you are using a 1541 type disk),
then store it in a safe place.  *Never* work with the original, just in
case something goes wrong.

None of the disk files are copy-protected, so there is no worry about
anything not working correctly with a backup disk.

If you are copying with more than one drive, Copy-all, a great
public-domain program by Jim Butterfield, is included on the disk to
assist you in doing this.  Copy-all will copy PRG, SEQ, and REL files
with no problems whatsoever on any type of Commodore compatible drives
using two drives.

If you need to copy REL files using a single 1541 drive, you can use a
program by Jim McAndrew called “Rel-Copy” specifically designed for that
purpose.<span id="anchor-162"></span>If you need to copy REL files using
a single 1541 drive, you can use a program by Jim McAndrew called
“Rel-Copy” specifically designed for that purpose.

<span id="anchor-163"></span><span id="anchor-164"></span><span id="anchor-163"></span>Designating Drives
---------------------------------------------------------------------------------------------------------

IMAGE BBS is designed to use up to eight drives, and possibly use even
more with limited functions.  It will support:

-   single or dual drives
-   Lt. Kernal logical units (LUs) 0 through 10 (the DOS LU, a side
    effect of applying the "CMD Mods" in Image BBS v1.2a—which, among
    other things, let the BBS access partitions numbered 1-255)

You will want to plan your setup on what space you have available, so
read the following information carefully to help you in this regard.

Although it is possible to run Image BBS using only one 1541 disk drive,
we highly recommend you use at least two, since you will find that disk
and directory space gets used quickly.

**Trust the docs when they say this.  I suffered with one 1541 for
years, then broke down and got a second one.  It still wasn't very
useful without having 30 sets of floppy disks, because I ran a huge
BBS.**

When referring to "device," we mean the device number assigned to the
particular drive (i.e., one drive online is usually set to device 8, two
to 8 and 9, etc.).

When referring to "drive," we are talking about the drive number (or
partition if using a hard drive):

-   0/1 on a dual drive such as the MSD-2 floppy drive

<!-- -->

-   partition 0-10 on a Lt. Kernal hard drive
-   partition 1-255 on a Creative Micro Designs hard drive (0 refers to
    the current partition)
-   If you have two physical drives, there may either be a switch
    somewhere on the drives to change device numbers, or—as with older
    1541 drives—you must cut a solder pad (the drive manual should
    describe how).

You may also “software change” the device number with the BASIC program
*dv change* included on your IMAGE BBS disk, or online with the <span
id="CD command"></span>You may also “software change” the device number
with the BASIC program *dv change* included on your IMAGE BBS disk, or
online with the *CD* command.  If you only have single drives on your
system, then the drive numbers will always be zero.

“Directory space” refers to the number of directory entries available on
the drive, which is usually limited, depending on the type of disk
drive.  A 1541 drive allows 144 directory entries, while an SFD allows
244, etc.  Check your drive manual to see what the limitation is.

<span id="anchor-165"></span>“Drive space” or “blocks free” mentioned here will refer to actual blocks used/unused on the drive.
================================================================================================================================

Now you will want to plan out which disks you want to use for which
functions on the BBS.  There are six “designated disks” for BBS
functions.  These can be combined in any form on any drive or number of
drives.  They are described as follows:

1: The “system” disk

Contains mostly SEQuential (text) files that do *not *change often. Menu
files, sub-board entry files, and other text/graphics files are all
included on this disk.  Also, BBS news files are located here.  Will not
use too much directory or drive space.

<span id="anchor-166"></span>System filenames on this disk start with *s*.
==========================================================================

<span id="anchor-167"></span>News filenames start with *n*.
===========================================================

2: The “e-mail” disk

<span id="anchor-168"></span>Contains all user e-mail and forced e-mail files (see page .  Will use much more directory space than disk space.
==============================================================================================================================================

<span id="anchor-169"></span>E-mail filenames start with *m*.  Forced e-mail filenames start with *f*.
======================================================================================================

If your BBS is part of a network, the NetMail files are stored here.
These may take up a significant amount of drive space, but not too much
directory space.

<span id="anchor-170"></span>NetMail filenames start with *nm*.
===============================================================

3: The “etcetera” disk

Contains miscellaneous files used to supply BBS information.  Many
online games and functions use one or more of these files to store their
data.  Some of these files are RELative files, and most of them change
frequently.  Storage depends on the number and type of online games and
programs you are using.  If no online programs use the etcetera disk, it
will not use too much disk or directory space.

<span id="anchor-171"></span>Etcetera filenames start with e.
=============================================================

4: The “directory” disk

Contains all directories used on the BBS, whether for sub-boards, U/D
libraries, text file libraries, or similar.  These files change often,
and this disk will use a fair amount of directory space, but not too
much disk space.

<span id="anchor-172"></span>Directory filenames start with d.
==============================================================

5: The “plus file” disk

Contains all BASIC or ML modules needed to run the BBS.  They load when
needed to execute various functions.  None of these files will change,
unless modified offline.

Plus file filenames start with several different prefixes based on these
categories:

*+.*BASIC modules

*++*ML modules

*scn.*top and bottom sysop screen displays (idle screen, online user
screens, Image Terminal screens)

In this revision of Image BBS, the Extended Command Set extension is
enabled by default. This gives the sysop more flexibility in several
areas. For more information on the ECS system, see page
[59](#anchor-173).

The initial *ml.ecsdefs* definition file which the ECS system needs
should be copied here also.

6: The “user” disk

Contains all user data files, which are expanded as new users sign on.
There are two files that keep all user information available to the
BBS.  Two directory entries, a little over one block per user total.

<span id="anchor-174"></span>User data filenames are *u.config* (REL) and *u.index* (PRG).
==========================================================================================

Different devices and drives can also be assigned to each of the
following:

-   Sub-board in the message base subsystem
-   Upload/Download or user exchange library in the file transfer
    subsystem
-   Plus file in the online programs subsystem
-   Movie file in the movie file subsystem
-   Text file in the text files subsystem

These need not be the same as any of the six pre-defined system drives,
but the above types of files may also be stored on those drives if so
desired.

### <span id="anchor-175"></span><span id="anchor-176"></span><span id="anchor-175"></span><span id="anchor-177"></span><span id="anchor-175"></span><span id="anchor-176"></span><span id="anchor-175"></span><span id="anchor-178"></span><span id="anchor-175"></span><span id="anchor-176"></span><span id="anchor-175"></span><span id="anchor-177"></span><span id="anchor-175"></span><span id="anchor-176"></span><span id="anchor-175"></span>Copying Files

Now, format a new or usable fresh disk (or partition if using a
mass-storage device) for each system drive you will have online, and
copy over the files from the disk that you backed up.  We also suggest
that you label each floppy disk with the device and drive number so that
you will not get confused as to its purpose.

**Unfortunately, Image is somewhat hobbled by a “flat file
structure”—i.e., there is no provision for using subdirectories (or even
partitions with 1581 drives) on mass-storage devices which support them
(the CMD devices are a good example).  All files must reside in the root
directory to be accessible.  This is a shortcoming I plan on addressing
in Image BBS 2.0 with the additions of CMD hardware detection (plus any
other hardware sysops give me reference material for) and the ability to
issue DOS commands where appropriate in what is called the "General
Files" section (which can have message bases, text and plus-file
subdirectories in a single directory!).\
\
A similar modification is possible for Image 1.2b, I just haven't gotten
much further than the planning stage; which is to say, just a bit
further than the BBS editor quoting... sigh.**

### <span id="anchor-179"></span><span id="anchor-180"></span><span id="anchor-179"></span><span id="anchor-181"></span><span id="anchor-179"></span><span id="anchor-180"></span><span id="anchor-179"></span>Setting Up Your Image BBS

We'll start by copying the files which the BBS needs to function to
their proper system disks.

### <span id="anchor-182"></span><span id="anchor-183"></span><span id="anchor-182"></span>Boot Disk

-   (Note: When you boot your BBS, any device can be used, but you
    *must* use drive \#0.  If you wish to use a different drive number
    to boot, you must change *setup* to reflect the proper drive.)

    If you are using a floppy-based setup, you need to make a “boot
    disk,” from which you will load your IMAGE BBS.  Just use a blank
    disk, and copy the following files onto it.  This disk is used
    whenever you are re-loading (booting) your BBS.

-   Whether you're using a floppy disk or hard drive partition, copy the
    following files to the device you want to boot from:

  -------------------- ---------------------------------------------------------------------------------------------------
  -------------------- ---------------------------------------------------------------------------------------------------

-   -   -   -

-   Copy to the System disk all files beginning with *s*.
-   Copy to the Etcetera disk all files beginning with *e*. (Note: the
    REL *e.say* file is optional.  This file contains "sayings"
    displayed to the user both at logon and when *SY* is entered at the
    main prompt.  Due to the size of this file, some sysops with smaller
    systems may wish to copy over *e.say-smaller* as *e.say*, or not use
    this feature at all by omitting the file entirely.)
-   Copy to the Plus File disk all files beginning with *+.* (don't
    forget *+.modem*), *++*, and *scn*. Also, *ml.ecsdefs* should be
    copied here in order for the default Extended Command Set
    definitions to work properly upon bootup.
-   The user files are written during the first-time configuration
    process, directory and e-mail files after your BBS is up
    and running.

**If you are using a user port modem, rename *ml.rs232/user* to
*ml.rs232*. If you are using a high-speed modem or telnet bridge
program, rename *ml.rs232/swift* to *ml.rs232*. *Config *may be modified
in the future to make this procedure automatic.**

It is fine to put these boot files on your System disk, assuming you
have sufficient drive space.

  -------------- ---------------------------------------------------------------
  -------------- ---------------------------------------------------------------

Table 4: Required plus file disk files

<span id="anchor-186"></span>Now you are ready to configure IMAGE BBS!
======================================================================

<span id="anchor-187"></span><span id="anchor-188"></span><span id="anchor-187"></span><span id="anchor-189"></span><span id="anchor-187"></span><span id="anchor-188"></span><span id="anchor-187"></span><span id="anchor-190"></span><span id="anchor-187"></span><span id="anchor-188"></span><span id="anchor-187"></span><span id="anchor-189"></span><span id="anchor-187"></span><span id="anchor-188"></span><span id="anchor-187"></span>Setting Up Your Image BBS
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<span id="anchor-191"></span>For many this is a new experience.  You
will not be reconfiguring an existing system nor be converting a system
over, but rather are starting from scratch.  For those that want or need
to start fresh, the Configuration Editor will do the job.  If you are
converting an existing system from CNet 12.0/12.1, there are also
convert routines in this program.

### <span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span><span id="anchor-194"></span><span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span><span id="anchor-195"></span><span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span><span id="anchor-194"></span><span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span><span id="anchor-196"></span><span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span><span id="anchor-194"></span><span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span><span id="anchor-195"></span><span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span><span id="anchor-194"></span><span id="anchor-192"></span><span id="anchor-193"></span><span id="anchor-192"></span>The Configuration Editor

Bla bla, some sort of intro.

### <span id="anchor-197"></span><span id="anchor-198"></span><span id="anchor-197"></span>Configuring a New System

You begin by loading the configuration program from your back-up disk.
Use the standard Commodore *load* command (assuming 8 is the device
number you're booting from):

<span id="anchor-199"></span>*load"config",8*
=============================================

After it is loaded, type *run*. The configuration editor is very
complete and self-documenting.  You should follow each step in sequence
just as they are listed in the configuration menu.

### <span id="anchor-200"></span><span id="anchor-201"></span><span id="anchor-200"></span><span id="anchor-202"></span><span id="anchor-200"></span><span id="anchor-201"></span><span id="anchor-200"></span><span id="anchor-203"></span><span id="anchor-200"></span><span id="anchor-201"></span><span id="anchor-200"></span><span id="anchor-202"></span><span id="anchor-200"></span><span id="anchor-201"></span><span id="anchor-200"></span>Device/Drive Assignments

The first menu selection helps define the devices and drives you have to
run your BBS on.  Selecting the DEVICE/DRIVE menu option will bring up a
sub-menu of options.  The system of sub-menus will take you completely
through your device and drive setup, defining each of the six required
system drives, identifying which device and drive they are set to, as
decided earlier.

The default values are for device 8, drive 0. To select an option, use
the *CRSR up* and *CRSR down* keys. To change the value the highlight
bar is on, hit *RETURN*. Use this procedure with any menu item in the
configuration editor.

### <span id="anchor-204"></span><span id="anchor-205"></span><span id="anchor-204"></span><span id="anchor-206"></span><span id="anchor-204"></span><span id="anchor-205"></span><span id="anchor-204"></span><span id="anchor-207"></span><span id="anchor-204"></span><span id="anchor-205"></span><span id="anchor-204"></span><span id="anchor-206"></span><span id="anchor-204"></span><span id="anchor-205"></span><span id="anchor-204"></span>Message Base, Upload/Download / Exchange Setup

**Since th**is** configuration editor was written, New Image Software
developed improved handling regarding these sections. **Called the
TurboRELs,** **t**hey **can be** configured while on the BBS via the
“RELedit” system. **(If you'd like to join the BBS network, you must use
this.) See “**[The RELedit System](#anchor-208)**,” page
**[26](#anchor-208)** for more** information.**

### <span id="anchor-209"></span><span id="anchor-210"></span><span id="anchor-209"></span><span id="anchor-211"></span><span id="anchor-209"></span><span id="anchor-210"></span><span id="anchor-209"></span>Access Levels

You must then assign access to each of your boards/libraries.  Access is
calculated using the following method, which is used throughout the BBS.
To determine which groups can access a given sub-board/library, add the
group’s access value:

*Group \#   Value  Group \#   Value*

*-------   -----  -------   -----*

*Group 0     1    Group 5     32*

*Group 1     2    Group 6     64*

*Group 2     4    Group 7    128*

*Group 3     8    Group 8    256*

*Group 4    16    Group 9    512*

#### <span id="anchor-212"></span><span id="anchor-213"></span><span id="anchor-212"></span><span id="anchor-214"></span><span id="anchor-212"></span><span id="anchor-213"></span><span id="anchor-212"></span>An Example

If you wished groups 3, 5, 7, and 9 to access a given board, you would
add:

> *Group \#   Add*

> *------- ---*

> *Group 3     8*

> *Group 5    32*

> *Group 7   128*

> *Group 9   512*

> *          ---*

<span id="anchor-215"></span>*   Total: 680*
============================================

<span id="anchor-216"></span>680 is what you would enter for the access code value.
===================================================================================

<span id="anchor-217"></span>*Note:* you may type ? at most prompts that ask for access levels and the BBS will go through groups 0-9, asking you if that group gets access (type Y for yes, other keys mean no). It then calculates (but doesn’t immediately display) the value for you.  You may do this in the configuration editor, or any part of the BBS that defines an access level.
============================================================================================================================================================================================================================================================================================================================================================================================

You also enter a *subop* (sub-board operator; a user given an area of
the BBS to maintain) for each sub-board/library.  This is done by typing
the ID number of the user desired.  If you are configuring a new BBS,
you have no users yet.  Therefore, assign the subop duties to either
yourself (user 1) or to no-one (user -1).  Of course, you may change
this later.

Each sub-board/library must be defined as to which device and drive to
put the files on (posts, responses, U/D files).  The device and drive
menu options allow you to set these.

When you're done with your selections, select the last option, "Keep
Parameters" and you are returned to the prompt to assign another
sub-board/library.  When you're done, simply select the "Main Menu"
option.

### <span id="anchor-218"></span><span id="anchor-219"></span><span id="anchor-218"></span><span id="anchor-220"></span><span id="anchor-218"></span><span id="anchor-219"></span><span id="anchor-218"></span><span id="anchor-221"></span><span id="anchor-218"></span><span id="anchor-219"></span><span id="anchor-218"></span><span id="anchor-220"></span><span id="anchor-218"></span><span id="anchor-219"></span><span id="anchor-218"></span>Editing Access Groups

You should now define your access groups.  There are ten groups, zero
through nine.  Each one can have different capabilities as you wish.
All new users signing on to the BBS are automatically placed into group
zero.  The parameters for each group consist of:

-   Group name
-   Number of calls permitted per day (1-254 or infinite \[0\])
-   Time in minutes permitted per call (1-99  or infinite \[0\])
-   Amount of time permitted idling (no activity at a command prompt)
    (1-9 minutes)
-   Number of downloads per call  (1-255 or infinite \[0\])

### <span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-225"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-226"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-225"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-227"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-225"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-226"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-225"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span><span id="anchor-224"></span><span id="anchor-222"></span><span id="anchor-223"></span><span id="anchor-222"></span>User Flags

Each group has a set of “flags” assigned to users placed in that group.
These flags may be customized for individual users at a later time if
desired.  With this editor, you set the flags as you wish them assigned
when first entering the particular group.  The flags usually toggle
between “Yes” or “No,” but a few require numeric input.

  ------------------------- --------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ------------------------- --------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------

Table : User flags

<span id="anchor-229"></span>

We also suggest that, at least to start, you define group 9 as the most
powerful group.  When you first log on to your BBS as sysop, you are
assigned group 9 access.  You may change your access group after logging
on for the first time.

When you have completed all assignments for a group, select the *Keep
Parameters* option and move on to another group.  When all groups are
assigned satisfactorily, choose *Return to Main Menu*.

*Note:* Any changes in access group information, either with the offline
*config* editor or the online *+.reconfig* editor, require a reboot
before the changes take effect.

<span id="anchor-230"></span><span id="anchor-231"></span><span id="anchor-230"></span><span id="anchor-232"></span><span id="anchor-230"></span><span id="anchor-231"></span><span id="anchor-230"></span><span id="anchor-233"></span><span id="anchor-230"></span><span id="anchor-231"></span><span id="anchor-230"></span><span id="anchor-232"></span><span id="anchor-230"></span><span id="anchor-231"></span><span id="anchor-230"></span>BBS Information
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Now you get to identify your BBS.  Select the *BBS Info* option from the
main menu.  It has several specific questions about you and your BBS to
help personalize it.

First, the sysop's information:

You are asked for the handle you have chosen to use on your BBS.  This
information is assigned to user number one, the sysop account.

You are also asked to provide a password. Choose it carefully since this
is usually the most powerful account on the BBS, and you will not want
it compromised.

Then you are asked a few other questions that are added to the data in
your account to start the user file.  This information can be changed
inside the BBS later, if you desire (using the *ED* or *EP* commands).

  ------------------ ---------------------------------------------------------------------------------------------------------------------------------
  ------------------ ---------------------------------------------------------------------------------------------------------------------------------

Table : BBS setup information

<span id="anchor-234"></span><span id="anchor-235"></span><span id="anchor-234"></span>Prime Time
-------------------------------------------------------------------------------------------------

A period where everyone is limited to being online a certain number of
minutes, and U/D access is limited to users with the “U/D at Prime Time”
flag set.  If you are just starting out, you may wish to wait to see how
busy your BBS is before setting up Prime Time.

If you decide to set it up, you are asked for:

-   The time to start
-   The time to end
-   The number of minutes you will permit users to stay online

<span id="anchor-236"></span>This information may be changed later if you wish.
===============================================================================

<span id="anchor-237"></span>When you are finished with the Prime Time option, choose *Keep Parameters* to return to the *BBS Info* menu.
=========================================================================================================================================

<span id="anchor-238"></span><span id="anchor-239"></span><span id="anchor-238"></span>Main Prompt
--------------------------------------------------------------------------------------------------

This is a message users see when they are not in any particular
subsystem.  It can be anything you want, but should be short. The
default prompt is *IMAGE:*

After establishing your prompt, return to the *BBS Info* menu.

<span id="anchor-240"></span><span id="anchor-241"></span><span id="anchor-240"></span>Credit Points
----------------------------------------------------------------------------------------------------

Credits are points that users accrue or lose depending on their actions
on the BBS. They earn more by uploading files, posting bulletins in the
message bases, playing games, the credit exchange and possibly by other
methods. They can also be awarded by the sysop for no good reason! The
final selection here is to set the number of credit points new users
receive when first signing up to your BBS.  This can be from 0 to
65,000, but we assume most sysops will not want to assign that many to
new users.

This completes the *BBS Info* section of your configuration!

<span id="anchor-242"></span><span id="anchor-243"></span><span id="anchor-242"></span><span id="anchor-244"></span><span id="anchor-242"></span><span id="anchor-243"></span><span id="anchor-242"></span><span id="anchor-245"></span><span id="anchor-242"></span><span id="anchor-243"></span><span id="anchor-242"></span><span id="anchor-244"></span><span id="anchor-242"></span><span id="anchor-243"></span><span id="anchor-242"></span>Loading Configuration Files
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

You may load configuration files at any time to make changes to them as
you desire.  This can also be done online with the *+.reconfig* program,
but the option is included here for any that may wish to reconfigure
their BBS off-line.

<span id="anchor-246"></span><span id="anchor-247"></span><span id="anchor-246"></span><span id="anchor-248"></span><span id="anchor-246"></span><span id="anchor-247"></span><span id="anchor-246"></span><span id="anchor-249"></span><span id="anchor-246"></span><span id="anchor-247"></span><span id="anchor-246"></span><span id="anchor-248"></span><span id="anchor-246"></span><span id="anchor-247"></span><span id="anchor-246"></span>Saving Configuration Files
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The last option is to save the configuration files to disk.  You are
first prompted to insert all system disks into their proper drives, and
then the files are saved to the disks.  You are notified if any file(s)
have not been written to disk, or if re-writing a particular file will
re-start the user log, before exiting the configuration editor.

<span id="anchor-250"></span><span id="anchor-251"></span><span id="anchor-250"></span><span id="anchor-252"></span><span id="anchor-250"></span><span id="anchor-251"></span><span id="anchor-250"></span><span id="anchor-253"></span><span id="anchor-250"></span><span id="anchor-251"></span><span id="anchor-250"></span><span id="anchor-252"></span><span id="anchor-250"></span><span id="anchor-251"></span><span id="anchor-250"></span>All Done
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

This completes the configuration of the BBS!  You can now select *Exit
Configuration Editor* and choose the appropriate option:

<span id="anchor-254"></span>*Return to BASIC*
==============================================

> *Cold start the machine*

> *Boot IMAGE BBS*

(If you change your mind, you can still escape with ←.) For now, let's
select *Return to BASIC* and continue with setting up the modem.

<span id="anchor-255"></span><span id="anchor-256"></span><span id="anchor-255"></span><span id="anchor-257"></span><span id="anchor-255"></span><span id="anchor-256"></span><span id="anchor-255"></span><span id="anchor-258"></span><span id="anchor-255"></span><span id="anchor-256"></span><span id="anchor-255"></span><span id="anchor-257"></span><span id="anchor-255"></span><span id="anchor-256"></span><span id="anchor-255"></span>Modem Configuration
======================================================================================================================================================================================================================================================================================================================================================================================================================================================================

You can run a dial-up BBS (and in fact some people still do), but for
convenience's sake, and to get the most callers possible, you'll
probably want to have incoming connections via the Internet.

If you're using a real Commodore 64, you'll be using an interface which
plugs in to either the user port (for example, an Omnitronix RS232
interface), or expansion port (a Turbo232 or Glink interface). A serial
cable connects to a PC which runs TCP/IP to RS232 “bridge” software,
allowing the BBS to send and receive modem commands and BBS data even
though there's not a real modem connected.

If you're hosting your BBS via an emulator...

<span id="anchor-259"></span><span id="anchor-260"></span><span id="anchor-259"></span><span id="anchor-261"></span><span id="anchor-259"></span><span id="anchor-260"></span><span id="anchor-259"></span><span id="anchor-262"></span><span id="anchor-259"></span><span id="anchor-260"></span><span id="anchor-259"></span><span id="anchor-261"></span><span id="anchor-259"></span><span id="anchor-260"></span><span id="anchor-259"></span>modemconfig 19.2
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

This program configures the modem to be used with the BBS through a
series of questions, which are outlined in the following section.
First, a preview of what it looks like:

<span id="anchor-263"></span>*Image 1.2 Modem Configuration*
============================================================

> **

> *   1 -- 1670  (Old Model)*

> *   2 -- 1670a (New Model)*

> *   3 -- Hayes 1200 (ATA)*

> *   4 -- Hayes 1200 (DTR)*

> *   5 -- Hayes 1200 (ATA/DTR)*

> *   6 -- Hayes 1200 (ATA/Reverse DTR)*

> *   7 -- Hayes 2400 (ATA/DTR)*

> *   8 -- Hayes 2400 (ATA/Reverse DTR)*

> *   9 -- Supra 2400*

> *  10 -- Aprotek 2400*

> *  11 -- Hayes 9600 (ATA/DTR)*

> *  12 -- Hayes 9600 (ATA/Reverse DTR)*

> *  13 -- Supra 9600 (ATA/DTR/X4)*

> *  14 -- Hayes 19.2k(ATA/DTR)*

> *  15 -- Hayes 19.2k(ATA/DTR/X4)*

> *  16 -- Customized*

> **

<span id="anchor-264"></span>*Modem Type? \[\]*
===============================================

<span id="anchor-265"></span>Type 16 (Customized) is the one you'll want for operation with a telnet bridge program.
====================================================================================================================

<span id="anchor-266"></span>Here is a summary of options presented when that choice is made:
=============================================================================================

1\. Baud rate0 = 300 ... 5 = 19200

<span id="anchor-267"></span>Pick the highest rate your modem or telnet bridge supports.
========================================================================================

2\. 0 = Escape codes (+++)1 = Data Terminal Ready (DTR) hangup

> +++ escape codes are used mostly on older modems such as the Commodore
> 1670.  Hayes-compatible modems usually support the DTR line with the
> Commodore user port or an RS232 interface in the expansion port.

3\. 0 = Auto answer (*ATS0=1*)1 = Manual answer (*ATA*)

4\. 0 = ATH1 = No ATH



<span id="anchor-268"></span>This refers to whether your modem includes *ATH* in its command set.
=================================================================================================

5\. 0 = Local off-hook1 = Not

> When you are logged on to the BBS from the local console, should the
> modem be taken off-hook so people trying to call in get a busy signal?

6\. 0 = ATH01 = ATH

<span id="anchor-269"></span>This is just a matter of semantics: does your modem use *ATH* or *ATH0* to hang up?
================================================================================================================

7\. 0 = Hang-up in modem reset1 = Not

<span id="anchor-270"></span>Choose whether to hang up when resetting the modem.
================================================================================

8\. Value for *ATX*

> This controls the number of error reporting (1-4) codes used by the
> modem (*VOICE*, *ERROR*, etc.) It is usually left at 4.

  --------- ---------------- ------------------------------------------------------------------------------------------------------
  --------- ---------------- ------------------------------------------------------------------------------------------------------

Table : Typical modem result codes<span id="anchor-271"></span>Table :
Typical modem result codes

  ---- --------------------------------------------------------------------------------------------
  ---- --------------------------------------------------------------------------------------------

9\. DTR:0 = Normal1 = Reversed

> DTR (Data Terminal Ready) is a connection that tells the DCE (Data
> Communication Equipment, typically a modem) that the DTE (Data
> Terminal Equipment, typically a computer or terminal) is ready to
> transmit and receive data[^2]. Some modems have the logic reversed; if
> bringing DTR high (toggling it on) signals a disconnect, and then
> select "Reversed."

<span id="anchor-272"></span><span id="anchor-273"></span><span id="anchor-272"></span>Telnet bridge software
=============================================================================================================

<span id="anchor-274"></span><span id="anchor-275"></span><span id="anchor-274"></span>Jim Brain's *tcpser-1.0rc6*
------------------------------------------------------------------------------------------------------------------

Tcpser is a telnet bridge program which can interface with either a real
Commodore 64 via a serial cable, or an emulator. It can be downloaded
from:

<http://www.jbrain.org/pub/linux/serial>

### <span id="anchor-276"></span>Using a physical serial port

Even if you're using Windows, its COM*x*: nomenclature is replaced by
Linux's */dev/tty*x. COM1 is equivalent to */dev/ttys0*. This suggested
command line for tcpser means “use serial port 0, use incoming port
6400, report the modem connect rate at 19200kBPS, initialize the modem
with the following string, log events at level 7, and show incoming and
outgoing RS232 and TCPI/IP traffic.”

`tcpser -d /dev/ttyS0 -p 6400 -s 19200 -i"e0v0h0x4&C1&D2&K3" -l7 -tSsiI`

### <span id="anchor-277"></span>Using the VICE emulator

*Note:* VICE doesn't emulate the CD (carrier detect) line if you're
using a user port modem. So while the BBS will answer, it won't
necessarily hang up properly if a user should disconnect midway through
their call.

Here, the `-d` parameter is replaced by `-v`, which is the port VICE is
listening on in its RS232 settings. Here is a command line to try:

`tcpser -i “e0v0” -s 2400 -v 25232 -p 6400`

If you're using a high-speed expansion port interface, you can increase
the `-s` value to something more appropriate.

<span id="anchor-278"></span>tcpser4j
-------------------------------------

This is the same thing as tcpser, except written in Java. You configure
it via an XML file (there is a well-documented sample file included),
then have the included `.bat` (Windows batch) or `.sh` (Linux shell script)
file reference that XML configuration file.

<span id="anchor-279"></span>Leif Bloomquist's _BBS Server_
-----------------------------------------------------------

This is a Windows program designed to allow a real Commodore 64 to run
Image BBS.

If you use this program and you have trouble getting the BBS to answer,
here's some information from Larry “X-TEC” Hedman:

> Jeff, I experienced the same problems you described when I started using
BBS Server with an Omnitronix RS232 interface plugged into the modem
port. I never could get it to work at any of the 2400 baud settings but
1200 baud works fine and connections say connected at 1200 baud but in
actuality, the speed is much faster.

> On my Image 1.0 version, I am using the Avatex 1200 *+.modem* file. If
using 1.2a I think I used the 1670 modem file but you can try any of the
1200 baud modem files until you find one that works. In BBS Server, you
must build and use the TelBBS Standard Cable as described in the docs.

> On the Comms page, set for *1200,N,8,1*. Set the serial cable type to
option 1 and click on ***Set Defaults***. You should have check marks
for *Enable hardware flow control* and *ATE1 (local Echo)* set by
default.

On the _Connecting_ page set checkmarks on `Raise DTR when caller connects` and
`Send RING to BBS when Telnet caller connects`.

On the _Disconnecting_ page, check `Disconnect if BBS drops DCD`,
`Disconnect if BBS drops DSR`, `Send NO CARRIER to BBS on disconnect`,
`and Lower DTR when caller disconnects`.

On the _Diagnostics_ page, check mark `Detailed RS-232 Diagnostics Logging`
and `Detailed Hayes Emulation Logging`. This will give you much
information about what is going on with your RS232 communication between
the PC and the BBS in the Activity Log.

On the _Emulation_ page, checkmark `Allow Outgoing Calls`,
`Send this string when Telnet session connects: CONNECT`,
`Send Winsock error messages to Terminal Program` and `Enable Hayes Emulation`.

Click on `Save Changes` which will take you back
to BBS Server's status page. Make sure the IP address is set for the IP
of your PC running BBS Server and type in the Telnet Port you will be
using. The standard port is 23 but using port 23, you will experience
hundreds of spurious connect attempts all from Asian IP addresses.
You're better off to use a different port but for now just use 23 until
you can make connections successfully.

If all that is set up and Image is booted to the call waiting screen,
you should see red blocks for CTS and DCD and a green block for RTS. At
that point you should be ready to receive calls. Try connecting to the
BBS using whatever method you are using, and watch the RX and TX blocks.
If it doesn't work use a different 1200 baud `+.modem` file until you
find one that works. Hope this helps.

<span id="anchor-280"></span>*Telnet bridge hardware*
-----------------------------------------------------

*Since telnet bridges* *don't support BPS rate changes over telnet, you
need to rename a custom version of +.modem called +.modem/telnet. This
is locked at 14.4 KBPS *instead of how the original +.modem file stepped
through its BPS rates, issuing initialization commands at each
speed.**<span id="anchor-281"></span>*Since telnet bridges* *don't
support BPS rate changes over telnet, you need to rename a custom
version of +.modem called +.modem/telnet. This is locked at 14.4 KBPS
*instead of how the original +.modem file stepped through its BPS rates,
issuing initialization commands at each speed.**

<span id="anchor-282"></span>These interfaces plug into the Commodore
64:

<span id="anchor-283"></span>Link232
------------------------------------

Expansion port; plans are available at
<http://www.go4retro.com/projects/link232/>

<span id="anchor-284"></span><span id="anchor-285"></span><span id="anchor-284"></span>Lantronix UDS-10
-------------------------------------------------------------------------------------------------------

-   sends ATA immediately upon answer

<span id="anchor-286"></span>CometBBS
-------------------------------------

-   User port; available soon from <http://www.commodoreserver.com/>

<span id="anchor-287"></span>GLink232 interface
-----------------------------------------------

-   A SwiftLink clone available from <http://gglabs.us/>. X-TEC
    mentions: *Tell the seller it's for hooking up to an Image BBS. This
    makes sure all the control lines are wired correctly.*

<span id="anchor-288"></span><span id="anchor-289"></span><span id="anchor-288"></span><span id="anchor-290"></span><span id="anchor-288"></span><span id="anchor-289"></span><span id="anchor-288"></span>Booting Up
=====================================================================================================================================================================================================================

You are now ready to boot up your new IMAGE BBS and make your first
“call!”  Most likely you will want to explore and/or continue its
configuration, using included tools to:

  ------------------------------------------------------------ ------------------------
  ------------------------------------------------------------ ------------------------

First, insert your boot disk into the proper device.  (We assume device
\#8 here.)  Type:

<span id="anchor-293"></span>*load"image 1.2b",8,1*
===================================================

<span id="anchor-294"></span><span id="anchor-295"></span><span id="anchor-294"></span>Autobooting Systems
----------------------------------------------------------------------------------------------------------

Sysops with Lt. Kernal hard drives may rename *image 1.2b* to
*autostart* and have an auto-booting BBS.

Sysops with Commodore 128s and CMD hard drives may rename *image 1.2b*
to *copyright cmd 89*, if the partition selected at power-on contains
this file.

<span id="anchor-296"></span><span id="anchor-297"></span><span id="anchor-296"></span>First Boot
=================================================================================================

Now, sit back and let your BBS load up.  After you see the title screen,
the program does a bit of work, loading various files:

  ------------------------------------------------------------------------------------------- --------------
  ------------------------------------------------------------------------------------------- --------------

Table : Startup files

<span id="anchor-298"></span>

If your system files are on a different disk than your boot disk, you
are prompted to ***Insert all system disks and press RETURN***, where
you should do just that. If all goes well, you should reach the “idle
screen.”

System won't start? Need troubleshooting help? There's a good discussion
about files needed in “[The Boot Process](#anchor-299)” on page
[101](#anchor-299).

<span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span><span id="anchor-302"></span><span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span><span id="anchor-303"></span><span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span><span id="anchor-302"></span><span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span><span id="The Idle Screen"></span><span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span><span id="anchor-302"></span><span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span><span id="anchor-303"></span><span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span><span id="anchor-302"></span><span id="anchor-300"></span><span id="anchor-301"></span><span id="anchor-300"></span>The Idle Screen
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

This is shown when no user is connected to the BBS.  If no keys are
pressed for about ten seconds after the idle screen shows, the screen
will blank, protecting your monitor from burn-in.  (You may disable the
screen blanking: see "[The Lightbar](#anchor-304)," page
[2](#anchor-304) for more information.)

Press almost any key, or receive an incoming call, and the screen will
turn back on.

### <span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span><span id="anchor-307"></span><span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span><span id="anchor-308"></span><span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span><span id="anchor-307"></span><span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span><span id="Setting the Time"></span><span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span><span id="anchor-307"></span><span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span><span id="anchor-308"></span><span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span><span id="anchor-307"></span><span id="anchor-305"></span><span id="anchor-306"></span><span id="anchor-305"></span>Setting the Time

Unless your BBS clock is set automatically, you should see a flashing
message to ***Set Time!***  The message continues to flash until you do
so.  (The BBS runs fine if the time is not set but timestamps for news
items, message base posts, and such will be incorrect.)

**To automatically set the BBS clock at startup, see “**[Automatic CMD
Device Clock Set](#anchor-309)**,” page **[100](#anchor-309)**. This
shows you how to modify the *setup* program to poll CMD devices with
real-time clocks (and perhaps LtK drives).**

For now, we will assume you are setting the BBS clock manually.

To set the time and date, type *1* while at this idle screen. Type the
time and date at the following prompts:

For the day of the week, type one of the following numbers:

  ----------- -------------- ------------- -------------
  ----------- -------------- ------------- -------------

Type the month, date, and last two digits of the year at each separate
prompt.

Enter the hour (don't use military or 24-hour time), minute, and A or P
for AM/PM for each following prompt.

The top status line changes to reflect the entered date and time.  If
the information is correct, respond to the OK? prompt by typing y (and
press RETURN).  Type n (or any key besides y) if you have made a mistake
and need to re-enter the data; note that answers to prompts now reflect
what you just typed to minimize effort.

Now a large clock is displayed, and the BBS waits for a call.  At the
top of the idle screen are several items of interest:

### <span id="anchor-310"></span><span id="anchor-311"></span><span id="anchor-310"></span>The Status Line

This top information line is displayed whenever the screen is not blank,
no matter what the BBS is currently doing. It shows, from left to right:

-   The day of the week, date and system time

Depending on conditions on the BBS and what you or the user online is
doing, four different letters can appear next:

  --------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  --------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The clock and status letters are followed by the minutes and seconds
remaining for users while they are online.  (Since no one is online at
the idle screen, it shows ***00:00***.)  When you or a user logs in, the
number of minutes left is displayed.

100 minutes or more is considered “unlimited time,” and time remaining
changes to ***--:xx*** (***xx*** being seconds).

There can also be check marks in the left and right corners of this
line: the left check mark indicates the user is in Commodore C/G mode,
and the right check mark shows when a modem carrier signal is present.

### <span id="anchor-312"></span><span id="anchor-313"></span><span id="anchor-312"></span>Top Screen Mask

At idle, this area of information just underneath the status line shows
the handle of the last caller, followed by their logoff time, and the
time of the last log restart (LR).The window to the right shows the
number of accounts currently used in the user file (UR).

When a user logs on, these displays will change to show additional
information, described on page .

You may toggle this "screen mask" on or off using *F1*, or a programming
command (discussed in “[Other & Calls](#anchor-314),” page
[97](#anchor-314)).

Several functions are available at this screen from the console, which
are outlined in a menu if you press any key aside from a "command" key.
The functions are as follows:

  ----------- ---------------------------------- --------------------------------------------------------------------------------------------
  ----------- ---------------------------------- --------------------------------------------------------------------------------------------

<span id="anchor-318"></span>Table : Idle screen keys

  --------- ---------------------------------------------------------------------------------------------------------------------------------------------
  --------- ---------------------------------------------------------------------------------------------------------------------------------------------

### <span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-323"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-324"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-323"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-304"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-323"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-324"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-323"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span><span id="anchor-322"></span><span id="anchor-320"></span><span id="anchor-321"></span><span id="anchor-320"></span>The Lightbar

The fifth screen line is referred to as the "lightbar."  This line
monitors and changes many features of the BBS.  All are toggled by the
sysop at the console, or through a utility program (*+.lb move*,
discussed in "Miscellaneous Plus Files"; this is handy for remote
maintenance when you can't be at the console).

  --------------- ----------------------------------------------------------------------------------------------------------------
  --------------- ----------------------------------------------------------------------------------------------------------------

(If the screen has blanked itself due to inactivity, it is restored when
you receive a call or hit a key on the keyboard.)

The first of two pages shows as follows:

Sys   Acs   Loc   Tsr   Cht   New   Prt   U/D

These check marks tell the BBS to do various things.  The following
descriptions assume each check mark described is selected.

  ----- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ----- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Table : Lightbar, page 1

The second page of lightbar options is as follows:

<span id="anchor-325"></span>Asc  Ans  Exp  Fn5  Fn4  Fn3  Fn2  Fn1
===================================================================

  ----- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ----- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<span id="anchor-326"></span>Table : Lightbar, page 2

### <span id="anchor-327"></span><span id="anchor-328"></span><span id="anchor-327"></span><span id="anchor-329"></span><span id="anchor-327"></span><span id="anchor-328"></span><span id="anchor-327"></span><span id="anchor-330"></span><span id="anchor-327"></span><span id="anchor-328"></span><span id="anchor-327"></span><span id="anchor-329"></span><span id="anchor-327"></span><span id="anchor-328"></span><span id="anchor-327"></span>Bottom Screen Mask

Along the bottom two lines of the screen is yet more useful
information.  The line just below the text display area contains BBS
operating information in this order:

  ---------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ---------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Table : Bottom two screen line display

The last row on the screen has a Receive window (R:) which displays the
last 10 characters received from the modem.  When the “trace” function
is enabled as described in *fixme* on page *fixme*, the BASIC line number currently
executing appears in the left half of this window.

The center portion of the bottom line can display any sixteen characters
you wish.  Typical phrases include:

-   `*Image BBS 1.2b*` at system idle
-   The type of computer a caller is using when online
-   The reason for chat if a user online requests a chat session and you
    are unavailable.  The window also flashes until either you answer
    the page, or the user logs off
-   It is also available to display custom information (see “[Other &
    Calls](#anchor-314)” for more details)

The final section of the bottom line is the Transmit (T:) window.  This
displays the last 10 characters sent to the modem.

<span id="anchor-331"></span><span id="anchor-332"></span><span id="anchor-331"></span><span id="anchor-333"></span><span id="anchor-331"></span><span id="anchor-332"></span><span id="anchor-331"></span><span id="anchor-334"></span><span id="anchor-331"></span><span id="anchor-332"></span><span id="anchor-331"></span><span id="anchor-333"></span><span id="anchor-331"></span><span id="anchor-332"></span><span id="anchor-331"></span>Logging On
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

You're now ready to go on line and examine your new IMAGE BBS in
action!  You can log on and edit your s. files, configure any sub-boards
and U/D libraries, or just look around and get acquainted with its
features. You may log on either normally or use the "instant" logon
feature.

### <span id="anchor-335"></span><span id="anchor-336"></span><span id="anchor-335"></span>Normal Logon

-   Use the *F3* and/or *F5* key to highlight the Loc position on
    the lightbar.
-   Press *F7*, which puts a check mark on the left side of Loc.

This starts logging in from the console, and is called a "local login."
We suggest that if you have a telephone connected to your modem, take it
off the hook at this time.  That way, if an incoming call connects with
your modem but not the BBS (since you're on locally), the caller won't
assume something is wrong with the BBS.

When a user has logged on, either remotely or locally, the program's
copyright message and serial number are displayed.  With a remote login,
the user is prompted to hit their backspace (delete) key to detect
whether they are in Commodore color/graphics (hereafter abbreviated as
"Commodore C/G") mode, or ASCII mode.

Depending on which mode they are in, the file `s.login 0` (for ASCII), or
`s.login 1` (for Commodore C/G) is displayed. For simplicity's sake in the
following references, the character _x_ at the end of a filename will refer
to either the digit _0_ (this file is seen by ASCII callers) or _1_ (this
file is seen by Commodore C/G callers).

Then the user is asked to `Press RETURN/ENTER`.  Actually, `A` can
be typed to abort the start screen; you could mention that in the
*s.login x* files.

<span id="anchor-337"></span>If `RETURN` is pressed, the program will read the
disk file `s.start _x_`.
=====================================================================================================

Next, the BBS instructs the user:

`ENTER YOUR HANDLE OR _&lt;your board name&gt;_ ID:`

If the user has no account, or makes a mistake entering the information,
they are instructed to type `NEW`.

If a mistake is made logging in, and if a file called *s.errmail* exists
on the disk, the contents of this file are sent in an e-mail message to
the user, informing them of the mistake.  If they should get this
message in their mailbox, and they weren't the ones to make the mistake,
urge them to change their password.

A file called *e.telecheck* is either created or appended to, which
contains the login time and date, the missed security question, and the
correct answer.  This file is viewable using the `VF` (View Feedback)
sysop utility.

If the user has made four mistakes and has not entered `NEW` they are
logged off for excessive login attempts.

If the user has a "reserved" account, they can enter `RES` at the prompt
to enter the RES function of the new user program.

### Instant Logon

This feature is reserved for the sysop, for it can only be used from the
console.  It is meant for a fast, easy way for you to log on to your BBS
to do maintenance functions, posting, or anything you would normally do
on a call.

The main difference from a regular logon is that none of your stats will
be updated or saved to disk, and your last call date will be set to your
logon time.

To use the instant logon feature, type `I` at the ***Hit RETURN/ENTER***
prompt. You are prompted for your password, and immediately taken to the
main prompt.

### <span id="RES-Users">RES Users</span>

A RES, or REServed, user is one that you have set up an account for already
using the `RS` or `ED` commands on the BBS.  (Perhaps you won't be around to
validate the user, for example.  See the \\1 section for more
information.)

They are asked to type their RES ID number and password—which you should
provide them with when you set up their account—and then be taken
through the normal new user application.  When they are done, they are
logged on with the pre-approved access and credit points that you assign
to them.

### <span id="anchor-343"></span><span id="anchor-344"></span><span id="anchor-343"></span>NEW Users

If a user enters a handle that is not found in the user log, they are
asked if they want to log on as a new user using that handle.

If they type *Y*, the new user procedure is gone through, beginning with
the reading of the file *s.new user* (but skips the handle prompt).

The new login procedure consists of four parts:

I.  General information: handle, real name, password
II. Terminal parameters: computer type, column width, linefeeds, etc.
III. Miscellaneous questions: address, occupation, baud rate, etc.
IV. Personal statement: a chance to type a paragraph or two about
    themselves.  This is required; if aborted they are logged off
    without signing up as NEW.

Once the new user login procedure is completed, this user information is
put in new user feedback for you to view later with the *VF* command,
and they are taken into the BBS with access group zero status.

### <span id="anchor-345"></span><span id="anchor-346"></span><span id="anchor-345"></span>Existing Users

If a user enters a handle that already exists, plus a password, then
they are asked a random security question:

-   Their first or last (real) name
-   Sections of their phone number: 3-digit area code, 3-digit dialing
    prefix, or 4-digit suffix

> `xxx-yyy-zzzz` is a format used in the USA and Canada; other countries
have differing formats.  For now, foreign callers can just make up a
phone number: `000-000-0000` works.  In Image BBS v2.0, this will change:
perhaps be made optional, or at the very least more configurable.  It
knows whether the sysop is in PAL- or NTSC-land, plus does timezone
offsets, so maybe that will figure into the equation.

This is used as an extra security measure.  If this question is missed,
the same procedure regarding the *s.errmail* and *e.telecheck* files
above is taken.

### <span id="anchor-347"></span><span id="anchor-348"></span><span id="anchor-347"></span><span id="anchor-349"></span><span id="anchor-347"></span><span id="anchor-348"></span><span id="anchor-347"></span><span id="anchor-350"></span><span id="anchor-347"></span><span id="anchor-348"></span><span id="anchor-347"></span><span id="anchor-349"></span><span id="anchor-347"></span><span id="anchor-348"></span><span id="anchor-347"></span>The Top Screen After Logon

Once a user has logged on and their password is verified, the top of the
sysop screen changes quite a bit from what it shows at the idle screen.

The very top line is the same as discussed in the section "The Status
Line."

The next five lines contain specific information about the user logged
on:

-   -   First is the user's handle, login ID (including the two
        character BBS identifier), last call date, and number of calls
        today and total to the BBS.
    -   Next is the user's real name, their access group, phone number
        and five flags--the first four are single digits--which include:

        -   Expert mode (0=off, 1=on)
        -   Color/graphics mode (0=ASCII, 1=Commodore)
        -   Linefeeds (0=off, 1=on)
        -   Default file transfer protocol (fixme...)
        -   Column width (between 22 and 80 characters wide)

Once a user has successfully logged on to the BBS, either remotely or
locally, as either a new user or a user with a login ID and password
already, the BBS reads the file entitled `s.welcome _x_`, and informs them
of:

-   what their access group is
-   how many calls they can make on that particular day (if not an
    infinite number)
-   the amount of time they have for this call

Then it will check for:

  -- -----------------------------------
  -- -----------------------------------

Table : Login activities

Once all of this has been completed, the user is placed at the main
command level.

### <span id="anchor-351"></span><span id="anchor-352"></span><span id="anchor-351"></span>Editing BBS Info Files

You now should be at the main command level, where you can do many
things.

Since this is your first call, you may wish to edit the following files
to suit your own tastes and coincide with your BBS plans.  Sample files
have been included on the disk, but may be edited or replaced with
whatever you wish.

While at the main command prompt, you can use the WF command (see
“[Write File](#anchor-353),” page [62](#anchor-353)) command for this.
It will give you access to a line-oriented text editor you can use to
edit files. If you have files other than ones included on the setup
disks you would like to use, you can import them into the text editor
using a “get file” dot command (type *.G* at the left margin).

*Be sure to type .C 80 return to set the editor line length to 80
characters before .Getting a file. Otherwise, lines with color/graphics
characters in them may exceed the 40-column line length, causing
word-wrap and ruining the file.*

**

> If that happens, type `.A Return` to abort your changes. Consider using
> an offline C/G screen editor such as *Kaleidoscope*, *Digital Paint*,
> *Tyron Paint* or similar.

**

Here is a summary of the files discussed in this section. Remember, the
suffix *x* stands for the digits 0 or 1, for ASCII or Commodore
Color/Graphics files, respectively.

  ---------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ---------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Table : Miscellaneous editable files

<span id="anchor-355"></span>

To create or edit these files, use the WF option (see “page
[62](#anchor-353)) at the main command level.  You can also use the .Put
and .Get options (page [Error: Reference source not found](#anchor-356))
in the editor. (See “[The IMAGE Text Editor](#anchor-291),” page
[45](#anchor-291) for more information.)

--- 8&lt; --- (snip)
------------------------------------------------------------

NOTE: THE NEXT TWO SECTIONS NEED NOT BE DONE IF YOU HAVE ALREADY
CONFIGURED YOUR SUB-BOARDS, LIBRARIES, AND ACCESS GROUPS WITH THE CONFIG
PROGRAM.

<span id="anchor-357"></span>BULLETIN BOARDS AND LIBRARIES:
===========================================================

After editing these files, you will want to set up your sub-boards and
U/D libraries if they have not yet been configured.  You can create up
to 30 sub-boards, 30 UD libraries, and 30 UX libraries.  To do this and
to change them at any time after, you can run the +.reledit program from
the main command level:

Type at the main prompt, then after the +. prompt, type reledit.

<span id="anchor-358"></span>ACCESS GROUPS
==========================================

You can define or change your access groups on-line if they have not
been previously defined.

At the main command level prompt enter R and run the file *access* at
the "+." prompt.  You can define up to 10 access groups and what they
can access on the BBS.  They are numbered from 0 (new user) to 9
(usually you, the sysop).  New users logging on are put in group 0.

For each of the group numbers that you choose to use, you can select a
title for it.  You should choose one of the access groups to be the
system operator group, for you with highest BBS privileges, For each
group you are using, you can select a specific amount of calls per day
that that group can make as well as how many minutes per call is
allowed, how many minutes at idle is allowed (how many minutes may pass
without pressing any keys before the BBS automatically hangs up), and
how many downloads can be made per call.

<span id="anchor-359"></span><span id="anchor-360"></span><span id="anchor-359"></span>Done!
--------------------------------------------------------------------------------------------

Now your IMAGE BBS v1.2b is ready to go on-line for calls!  You may wish
to post a few bulletins and news files to get the BBS started.

We hope you like your BBS, and welcome your comments and suggestions.

<span id="anchor-361"></span><span id="anchor-362"></span><span id="anchor-361"></span><span id="anchor-363"></span><span id="anchor-361"></span><span id="anchor-362"></span><span id="anchor-361"></span>General Commands
===========================================================================================================================================================================================================================

When you first log on to your BBS, after it checks for your mail, and
goes through normal logon procedures, you will be at the "main command
level."  You will see your main prompt that you defined in the
configuration editor.  You are now at the area where you have many
options as to what you will do next.

This chapter will deal with the commands needed to get to certain
functions of the BBS, and how to use them.

The following commands are considered "general" commands because they
are not specific to a particular subsystem.  They may be typed at the
main prompt, or most subsystem prompts as well.  A few commands (mostly
maintenance in nature) are available *only* from the main prompt, or
using local or pseudo-local mode.  These commands are discussed in the
"Maintenance" chapter.

The nice thing about general commands is the BBS remembers which
subsystem you came from, so you can return to it when done with the
current subsystem. For example, you have just finished viewing a
directory listing of files in the U/D subsystem, and wish to go to the
Voting Booth.  You type *VB* at the U/D subsystem prompt listing
directory information, and when you quit the Voting Booth, you will be
returned to the U/D subsystem.

Most general commands consist of two letters, sometimes followed by an
argument (parameter) of one or more numbers.

Examples:

SB Enter the message bases.  The BBS prompts the user which special
interest group or message area they would like to enter, depending on
what places they have access to.

SB1 Enter the message bases, but immediately go to the first Special
Interest Group they have access to.  They are prompted for the message
base to enter after that.

SB1,2 Enter the message bases, go to the first Special Interest Group,
and the second message base in that SIG with no further prompting.

**If you're a Trekkie, this reminds me of Klingon programmers: Their
programs do not **have** parameters, they have **arguments**, and they
always **win** them...**

A few commands consist of only one letter. Here are the descriptions of
the general commands and how to use them.

<span id="anchor-364"></span><span id="anchor-365"></span><span id="anchor-364"></span>Chat Request/Chat Mode
-------------------------------------------------------------------------------------------------------------

C requests a chat with the sysop.  A short (38 character) reason for
chat is requested; the first sixteen characters of that is displayed at
the bottom of the system screen.  This reason is also recorded in the
call log on disk and printer (if used).

If the left side of Sys is checked, the user is given a message
informing them that the sysop is being paged, and the BBS monitor sounds
three sirens.

If there is no checkmark, the user is told that you are not available.
The s.chat x file is shown, and they are asked if they want to leave
feedback instead.

The "reason for request" continues to flash until they log off or you
answer the chat page.  If the user requests chat more than once without
you answering the first chat request, they are told that the page is
already on, discouraging them from continuing to type C.

<span id="anchor-366"></span><span id="anchor-367"></span><span id="anchor-366"></span>Feedback
-----------------------------------------------------------------------------------------------

Feedback is "mail" left on the BBS to the sysop(s), that any user with
local or remote maintenance access may read.  It is left to the sysop(s)
by entering F at most prompts, or when logging off.  The user is placed
into the editor to write their message.

Any user, including a new user, is allowed to leave up to three feedback
messages per call.  If they try to leave more, they are informed they
have left their limit of feedback for that call.

Feedback, along with new user information and error messages, are read
by the sysop by typing VF at the main command prompt. (VF is described
more on page [63](#anchor-292).)

<span id="anchor-368"></span><span id="anchor-369"></span><span id="anchor-368"></span>Help
-------------------------------------------------------------------------------------------

? reads a menu of commands available at whichever command level the user
happens to be.  Depending on how much information is in the menu, a
"More?" prompt for additional command information may appear (although
this is put in the menu file itself, and is not always necessary,
depending on the file's length).  At this prompt, Y (meaning yes)
continues, most others mean no and stop reading the file.

If the user is not at the main prompt, the main menu is then read.

<span id="anchor-370"></span><span id="anchor-371"></span><span id="anchor-370"></span>BBS Information
------------------------------------------------------------------------------------------------------

CF shows the file s.config.  This file should contain general
information about your BBS, perhaps the hardware and software it runs
on, its hours (if not 24 hours a day) and anything else interesting
about it.

<span id="anchor-372"></span><span id="anchor-373"></span><span id="anchor-372"></span>Change/View Last Call Date/Time
----------------------------------------------------------------------------------------------------------------------

The *last call date* is used to determine which messages on the BBS are
new and which are old.  If a user is logged off before they have a
chance to see all new messages, they can use this command to move their
last call date back the next time they call.

<span id="anchor-374"></span><span id="anchor-375"></span><span id="anchor-374"></span>Log Off
----------------------------------------------------------------------------------------------

O will ask if the user really wants to log off (type Y to do so), asking
if they want to leave feedback first.

O% saves the last call date, in case they did not read all the new
messages in the message bases.

O! logs off instantly, without prompting for feedback.

O% and O! may be combined: 0%! logs off instantly and saves the last
call date.

<span id="anchor-376"></span><span id="anchor-377"></span><span id="anchor-376"></span>Quit
-------------------------------------------------------------------------------------------

From most prompts (and in some subsystems, just pressing Return) gets
the user to the main prompt.

If Q is entered at the main prompt, the user is asked whether they wish
to log off, as above.

<span id="anchor-378"></span><span id="anchor-379"></span><span id="anchor-378"></span>Time/Date
------------------------------------------------------------------------------------------------

T displays the current time, the time the user logged on, and the amount
of time remaining on the BBS this call.

<span id="anchor-380"></span><span id="anchor-381"></span><span id="anchor-380"></span>Edit Terminal Parameters
---------------------------------------------------------------------------------------------------------------

EP enters a menu which allows a user to change their computer type,
graphics translation mode, terminal line length, whether linefeeds are
required, toggle their expert mode, and change their account password.

<span id="anchor-382"></span><span id="anchor-383"></span><span id="anchor-382"></span>Prompt Mode
--------------------------------------------------------------------------------------------------

PM toggles prompt mode on or off. When on, when a user reads new
messages in the message base (using RN or RA commands), they do not
receive the "end-of-bulletin" prompt between message threads, or the
"\[P\]ost \[N\]ext \[Q\]uit" prompt between sub-boards.

Useful for callers who want to speed-read or buffer messages.

It also eliminates the prompt after the A (About this file) command in
the U/D subsystem.

<span id="anchor-384"></span><span id="anchor-385"></span><span id="anchor-384"></span>Status
---------------------------------------------------------------------------------------------

ST allows users to see their status on the BBS, including:

-   Their handle, plus real first and last name
-   Last call date and time
-   Their login ID
-   Their access level
-   Number of lines in the editor
-   Calls to the BBS, today and total
-   Downloads allowed (0=unlimited)
-   Number of uploads and downloads made
-   Number of blocks uploaded and downloaded
-   Credit points and credit ratio
-   Total posts and responses
-   User flags (see “,” page )

Then the user is asked if they wish to view this information again. If
not, they are returned to the BBS.

<span id="anchor-386"></span><span id="anchor-387"></span><span id="anchor-386"></span>SYSaying
-----------------------------------------------------------------------------------------------

Reads a random "saying" or "fortune," such as the one read at logon,
from the RELative file e.say.

<span id="anchor-388"></span><span id="anchor-389"></span><span id="anchor-388"></span>LGActivity Log
-----------------------------------------------------------------------------------------------------

Designated users may read the daily log, listing what activities callers
have done on the BBS.

<span id="anchor-390"></span><span id="anchor-391"></span><span id="anchor-390"></span><span id="anchor-392"></span><span id="anchor-390"></span><span id="anchor-391"></span><span id="anchor-390"></span>BABAR Stats
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Designated users may view the Board Activity Register stats as shown
between calls.  See "[Board Activity Register](#anchor-315)," page
[42](#anchor-315) for more details.

<span id="anchor-393"></span><span id="anchor-394"></span><span id="anchor-393"></span>ATC/G - ASCII - ANSI Mode Toggle
-----------------------------------------------------------------------------------------------------------------------

Chooses between Commodore Color/Graphics, plain ASCII, and ANSI
graphics.  This option is saved to the user file when logging out.

<span id="anchor-395"></span><span id="anchor-396"></span><span id="anchor-395"></span>XPExpert Mode
----------------------------------------------------------------------------------------------------

Toggles Expert Mode.  When on, subsystem and sub-board entry screens are
skipped.  This option is saved to the user file when logging out.

<span id="anchor-397"></span><span id="anchor-398"></span><span id="anchor-397"></span>NUNew User Message
---------------------------------------------------------------------------------------------------------

Re-read the s.new user file, read when a new user logs on to the BBS for
the first time.

<span id="anchor-399"></span><span id="anchor-400"></span><span id="anchor-399"></span>Local Mode
-------------------------------------------------------------------------------------------------

This allows users with local mode access to enter pseudo-local mode so
they can do maintenance functions remotely.  These functions include
copying files, reading directories, sending DOS commands, etc.  This is
very powerful, and should be given to only the most trusted users on
your BBS.

<span id="anchor-401"></span><span id="anchor-402"></span><span id="anchor-401"></span>Command Stacking
=======================================================================================================

Any of the main commands entered at any prompt can be "stacked" by using
the up arrow key (\^) between the commands. If the following command
were entered at the main prompt:

<span id="anchor-403"></span>*SB9\^RN\^&lt;\^R3\^UD\^SA*
========================================================

Then the BBS would

-   SB9Take you to sub-board 9
-   RNRead the new messages there
-   &lt;Move backwards, to sub-board 8
-   R3Read post \#3
-   UDEnter the U/D subsystem
-   SAScan for all new uploads

Certain places, such as choosing "quit" in the "end of bulletin" prompt,
usually clear stacked commands—if a user realizes they need to do
something in the middle of executing the stacked commands, their only
recourse is to hold down the spacebar to stop them.

See the "MACS" command on how to automate command stacking.

<span id="anchor-404"></span><span id="anchor-405"></span><span id="anchor-404"></span>Entering/Changing Subsystems
===================================================================================================================

Additional commands available at all major levels of the BBS include
those which go to any other subsystem.  In other words, a user need not
exit to the main command level from the sub-boards before going to U/D's
or PlusFiles, but can enter that area directly by typing the command.

Commands which behave this way include:

BBBulletin Board listings

EME-mail subsystem

MFMovie Files subsystem

NFNews Files subsystem

PFPlusFiles subsystem

SBMessage base subsystem

TFText Files subsystem

UDUpload/Download subsystem

ULUser Listings

UXUser Exchange subsystem

VBVoting Booth

Each of these commands take the user to a separate subsystem of the BBS,
which will be discussed in an upcoming chapter.

<span id="anchor-406"></span><span id="anchor-407"></span><span id="anchor-406"></span>Common Subsystem Features and Commands
=============================================================================================================================

Since several subsystems share similar commands and usage, this section
outlines them.

When a user enters the subsystem or a SIG, only the sub-boards/SIGs that
their access group can go to are loaded into memory.

So, if you have five sub-boards, but a user logs on with an access group
which can only access boards one and five, they'll see only two boards,
re-numbered as 1 and 2.  In this way, they aren't aware of other areas
they can't access existing.

<span id="anchor-408"></span><span id="anchor-409"></span><span id="anchor-408"></span>Listing Sub-Boards
---------------------------------------------------------------------------------------------------------

<span id="anchor-410"></span>A user can list which sub-boards they have access to when they first enter the SIG by
==================================================================================================================

typing *L* (optionally followed by the board number to start the listing
from)

If they are subop of a particular sub-board, the board name is preceded
with a "&gt;".

If you have set up Special Interest Groups, only SIGs the user has
access to are displayed.  In this way, they are not aware of areas they
cannot access.  When they get the "What SIG?" prompt, they may type
either:

-   The SIG number by itself
-   The SIG number, a comma, and the board number within that SIG (this
    works for SB, UD, and UX subsystems)

For example, if a user responded to the "What SIG?" prompt with "4,10",
they are taken into SIG \#4, Sub \#10 (or U/D \#10, etc.), assuming they
have access to it.

When a user enters a SIG number that is too high, the available SIGs are
re-listed, instead of exiting to the main prompt.

When a user enters a sub-board/library number that is too high,
available boards are re-listed.

Pressing RETURN/ENTER at the "Which Sub *(or U/D or U/X)*?" prompts
return the user to the list of available SIGs.  (If SIGs are not active,
they exit to the main prompt.)

### <span id="anchor-411"></span><span id="anchor-412"></span><span id="anchor-411"></span>NSub-Board Name

This displays the current sub-board's name.

### <span id="anchor-413"></span><span id="anchor-414"></span><span id="anchor-413"></span>Moving To Other Sub-Boards or SIGs

<span id="anchor-415"></span>A user can change the current sub-board by
=======================================================================

Entering the new sub-board number at the "Sub \#x: " prompt

"&lt;" or ";" takes then to the previous sub-board

"&gt;" or "=" takes them to the next sub-board

If a number is typed after the previous two commands, (ie, &gt;&gt;4 or
&lt;&lt;5) the user is taken to the previous/next SIG, plus the
specified board number.

If a user moves to a board they are subop of, they are informed of this.

If a move cannot be made, the user is told the board number they
requested does not exist.

<span id="anchor-416"></span><span id="anchor-417"></span><span id="anchor-416"></span>Sub-Boards (Message Bases)
=================================================================================================================

This is IMAGE BBS's public message base, where users can write messages
about anything they want, replying to other users in "threads" which
keep responses organized.  Users access message bases by typing *SB* at
most prompts.

If the user knows which SIG they want, they can combine the SB command
and the SIG number:

*SB3*This takes the user to SIG 3, assuming they have access.

If the user knows which SIG and sub-board they want, they can combine
the SB command, the SIG number, a comma, and the sub-board number:

*SB3,2*This takes the user to SIG 3, sub-board 2, assuming they have
access.

Upon entering the message bases, the file "s.SB" is read, regardless of
their expert mode setting.

If SIGs are set up, the SIG list is shown. They get a "Which SIG?: "
prompt.  As above, if the user knows which SIG and sub-board number they
want, they can enter them here, as above (example: 3 or 3,2).

Upon entering the board, they are told:

-   How many bulletins there are
-   How many have new responses since their last call date
-   Total number of responses

     8. The \[Q\]uit function (in the \[P\]ost \[N\]ext \[Q\]uit prompt)
now clears any stacked commands. This is for the people who have stacked
commands and then in the middle of reading the posts remembered they had
to do something (i.e., kill a post, weed the Subs, etc.) but were locked
into a command stack. Now they are not.

     9. Response titles are now available in the Subs.  Setting the
variable RT to 1 in line 901 of *+.MM.sb-post* will turn the ability to
title responses on (it comes with RT set to 1).  The response system is
100% compatible with older posts and NO CONVERSION IS NECESSARY.

     A new version of the *+.NM.netsub* files will soon be available
that allows the response titles to be transferred to other NetSub boards
as well as to allow "overflow" NetSubs to be defined.

Setting RT to 0 will NOT prevent any existing response titles from being
displayed, nor will it block NetSub response titles from being shown
once the new *+.NM.netsub* files are released.

The RT variable only controls the user's ability to title responses on
your board.

<span id="anchor-418"></span><span id="anchor-419"></span><span id="anchor-418"></span>Scanning Bulletins
---------------------------------------------------------------------------------------------------------

<span id="anchor-420"></span>This means to display
==================================================

-   The number of the bulletin
-   How many responses have been made, if any
-   The bulletin's status:

  --------- -----------------------------------------------
  --------- -----------------------------------------------

Table : Bulletin status indicators

-   The bulletin's title (in quotes)

Typing *S* begins scanning at either the first bulletin, or after the
bulletin most recently read on the sub-board.

S followed by a bulletin number starts scanning at that bulletin.

The slash (/) key or the space bar abort a scan at any time.

<span id="anchor-421"></span><span id="anchor-422"></span><span id="anchor-421"></span>About Bulletins
------------------------------------------------------------------------------------------------------

<span id="anchor-423"></span>This displays the
==============================================

-   Subject
-   Author (and node number if in a NetSub)
-   Date and time of creation
-   Number of responses to a bulletin
-   Date and time of the latest response

Typing tells a user about the bulletin following the one most recently
read or manipulated.

A followed by a number finds out about that specific bulletin.

<span id="anchor-424"></span><span id="anchor-425"></span><span id="anchor-424"></span>Reading Bulletins
--------------------------------------------------------------------------------------------------------

This displays the same information as the "about" function, but reads
the text body of the message, followed by each response until the end of
the *thread* (group of bulletins under that title).

Typing R (or just pressing RETURN) reads the next bulletin in the sub.

R followed by a number reads that specific bulletin.

While reading a bulletin, a user can:

Press the space bar to skip to the next response in the thread

Press "/" to skip directly to the end of the bulletin.

Once at the end of a bulletin, a user has several options in,
appropriately enough, the "end-of-bulletin" prompt.  (This prompt is
only displayed if the user's Prompt Mode is enabled.)

Press RETURN to continue to the next message in the sub-board

P sends a private e-mail message to the user that posted the original
message

R responds to the post

O reads the post over from the beginning

Q or "/" stops the RN or *RA* function

K lets a subop or sysop kill the post.  The original poster may also
kill the post, if there are no responses.

A question mark at this prompt brings up a menu of these options.

<span id="anchor-426"></span><span id="anchor-427"></span><span id="anchor-426"></span>New Messages
---------------------------------------------------------------------------------------------------

The following commands work on the current sub-board, with messages
considered new since the user's last call.  To do the following:

Scan .............. SN

Find out about .... AN

Read new .......... RN or \*

To stop an RN in progress, press the "/" key while reading a message.

To scan or read new messages on the current sub-board, plus all
higher-numbered sub-boards, type *RA* or *SA*, respectively.

To stop an *RA* or *SA* at the current sub-board, press the "/" key.

During an RA, if the user reaches the last board and has any stacked
commands remaining (for example, RA\^UD), the \[P\]ost \[N\]ext \[Q\]uit
prompt is displayed to allow the user to post to the last sub before
executing the next stacked command.

<span id="anchor-428"></span><span id="anchor-429"></span><span id="anchor-428"></span>Posting New Bulletins
------------------------------------------------------------------------------------------------------------

If a user types P and there is room in the directory (a limit of 60
posts per sub-board exists), the user is asked for the post's title. If
this title is unique to the directory, the user is asked:

If they wish to post anonymously, if the board is not set up to be
non-anonymous.  If they elect to post anonymously, the author will
appear as

Anonymous to normal users.

\* followed by the user's handle, to users with subop, sysop, or
sub-board maintenance access.

The user is then placed into the BBS text editor subsystem to write
their message.  .S on a blank line exits, as usual.

<span id="anchor-430"></span><span id="anchor-431"></span><span id="anchor-430"></span>Killing Entire Threads
-------------------------------------------------------------------------------------------------------------

This removes the original post concerned, along with all its responses,
from the sub-board and its message directory.

K begins listing all bulletins starting with the first one

*Kx* starts with bulletin \#x

The user is asked whether they want to kill the bulletin:

Y)es N)o A)bort or S)tart

K followed by a number begins the listing with that number, offering the
same choices.  Once the end of the list is reached (or S is typed), the
directory is re-written to disk.

A regular user can kill their bulletin only if there are no responses to
it.  Once responses are added, only a subop can kill it.

### <span id="anchor-432"></span><span id="anchor-433"></span><span id="anchor-432"></span>KO and KA

There are two more commands available to persons with SubOp access
(SubOps, Sub-board Maintenance and SIGOp access users).

KO Lists any messages in the SB section older than the maintainer's last
call date, giving them the option to kill them.

KA The same as KO, but is automatic - it will *not* ask if you want to
keep the post(s) killed, so be *very careful* with this command!

Remember, these commands are keyed to your last call date, so use LD to
set the cutoff date for deleting old messages *first*.

<span id="anchor-434"></span><span id="anchor-435"></span><span id="anchor-434"></span>Editing Bulletins
--------------------------------------------------------------------------------------------------------

To edit a previously written bulletin, enter E followed by the post
number to edit.  The bulletin is opened, and the BBS searches through
the bulletin for messages that the user can edit (if they are the
author, or sub-board operator).

If such a message is encountered, the user is prompted with:

K)eep, D)elete, R)ead, E)dit, or A)bort:

K)eepKeeps the message with the thread

D)eleteRemoves the message from the thread

R)eadReads the current message

E)editTake the user to the editor subsystem to edit the message

A)bortReturn the user to the sub-board prompt.

In the Edit function, SubOp access users have an added command: (K)ill
Old Resp.  This function first asks if you want to auto delete old
responses:

*No* asks for confirmation before deleting each response.  (*A* aborts
the operation, but any deleted responses *stay* deleted!)

*Yes* deletes any responses made before your last call date.

Both functions stop when they reach responses posted on or after your
last call date.  Remember, this function is tied to your last call date,
so use LD to set the cutoff date first.

Also remember, the Auto Delete function *cannot be aborted* once started
and is *only* available to SubOp access users!

<span id="anchor-436"></span><span id="anchor-437"></span><span id="anchor-436"></span>Frozen Bulletins
-------------------------------------------------------------------------------------------------------

If a user does not want responses added to a post, begin the title with
an up arrow (\^) character.  The BBS reports this bulletin as frozen
during a scan or About, and will not allow responses to be made to it.

Bulletins can be un-frozen by the original poster reading the message
with Prompt Mode enabled, so you get the end-of-bulletin prompt.  There,
type F, which toggles the bulletin's Frozen status.  The current status
is then reported, and the user is returned to the end-of-bulletin
prompt.

<span id="anchor-438"></span><span id="anchor-439"></span><span id="anchor-438"></span>Sub-Board Operators
----------------------------------------------------------------------------------------------------------

<span id="anchor-440"></span>V views the current sub-board's operator
=====================================================================

M sends a private e-mail message to them

<span id="anchor-441"></span><span id="anchor-442"></span><span id="anchor-441"></span>Maintenance Mode
-------------------------------------------------------------------------------------------------------

Only sub-board or users with general sub-board maintenance can access
this function.  Type Z.  The sub-board maintenance menu has two options:

1\) Edit the entry file.

You have a choice between ASCII and C/G.  A sub-board's entry file is
displayed upon entering the sub-board.  If there is an entry file
already, it is loaded into the BBS text editor. Use the usual editor
commands, and type .S to save.

2\) Edit board detail.

The user can change

Sub-board title

Sub-board type

Open/closed status

Access level required to enter the sub-board

If the user is in local or pseudo-local mode, they also have the option
to change the current sub-board operator and device/drive assignment.

While defining sub-boards using the +.reledit program, you may specify
any of your sub-boards to be:

### <span id="anchor-443"></span><span id="anchor-444"></span><span id="anchor-443"></span>Message Bases:

  ------ ------------------------- -----------------------------------------------------------------------------------------
  ------ ------------------------- -----------------------------------------------------------------------------------------

Table : Message base abbreviations

  -- --
  -- --

Table :

### <span id="anchor-445"></span><span id="anchor-446"></span><span id="anchor-445"></span>Upload/Download/Exchange:

  --------------- --------------------------------- -------------------------------------------------------------
  --------------- --------------------------------- -------------------------------------------------------------

Table : U/D and U/X types

<span id="anchor-447"></span>EITHER:
====================================

&gt; You’re the subop User has ability to edit/delete posts and
generally maintain the sub-board.

  \* A "password" board:

This requires a password to enter.  The BBS asks any user that has
access to that board for the password upon entering it.  If they get the
password wrong, they are asked if they want to try again.

If they guess wrong three times in the same call, they are not allowed
to guess again.  This can be used either for fun, by putting hints to a
password up other places in the BBS, or to add a measure of security for
certain boards that you do not want all users to access.

  \* An "anonymous" board:

All bulletins and responses will show as anonymous, even to the
sub-board operator and sysops.  Great for those "war boards."

  \* A "non-anonymous" board:

No anonymous messages are permitted, and users are not asked if they
would like the post/response to be anonymous.

<span id="anchor-448"></span><span id="anchor-208"></span><span id="anchor-448"></span>The <span id="anchor-449"></span><span id="anchor-448"></span><span id="anchor-208"></span><span id="anchor-448"></span>The <span id="anchor-450"></span><span id="anchor-448"></span><span id="anchor-208"></span><span id="anchor-448"></span>The <span id="anchor-449"></span><span id="anchor-448"></span><span id="anchor-208"></span><span id="anchor-448"></span>The RELedit System
=================================================================================================================================================================================================================================================================================================================================================================================================================================================================================

*This is from the documentation on *the TurboREL *disk, with slight
modifications.*

Image V1.2 REL SIG's Upload/Download, Exchange Subsystems

Thank you for selecting the new U/D and exchange systems for use on your
BBS.  Many long hours were put into this software to make it the best
system we could possibly offer.  This documentation provides you with
everything you need to know about the system, plus just a bit more.  It
consists of four general parts:

-   System Overview
-   Setup
-   Available commands
-   Sysop commands

<span id="anchor-451"></span>    <span id="anchor-452"></span><span id="anchor-451"></span>    Part One: System Overview
------------------------------------------------------------------------------------------------------------------------

The program makes available to you several new features which enhance
your BBS to its maximum potential, including:

-   Enhanced board types
-   Separate password for each board

    In the case of U/D's or U/X's:

-   Last download date
-   Local mode multi-uploads and downloads
-   Expanded "about" function
-   Online program reader

The User Exchange bases have all the same features above, plus:

-   The *E* command when downloading multiple files to select all files
    matching a selected pattern, with one easy keystroke.

<span id="anchor-453"></span><span id="anchor-454"></span><span id="anchor-453"></span>Part Two: General Setup
--------------------------------------------------------------------------------------------------------------

A few variables can be set in line 1 of *+.UD*: *yy%* and *it*.  (They
are currently defaulted to zero.)

-   Setting *yy%* to 1 deducts credits for files read online. Setting
    *YY%* to 2 deducts double credits, and so on.
-   Setting *it* to 1 freezes the user's remaining time on the BBS while
    they are in the U/D's, giving it back at exit.

Some more things to consider:

-   If you have no SIGs defined, you are limited to 30 board names.
-   With SIGs defined, you are allowed 999 board names (30 libraries
    per SIG).

<span id="anchor-455"></span><span id="anchor-456"></span><span id="anchor-455"></span>Part Three: Available Commands
---------------------------------------------------------------------------------------------------------------------

Toggling *Fn5*'s right check on, you activate the "no credit until
validated" feature of the BBS.  This check mark can be toggled on or off
any time a user is online and uploading, until the point the "End Of
Transfer" message appears.

-   If the check is off, the number of times downloaded is set to 0, and
    credits awarded to the user according to their credit ratio.

  \* If the check is on, the times downloaded is set to -1, but no
credits awarded until the file is validated by the subop or SIGop.

Toggling Fn5's left check on activates the "Log off after file transfer
complete?" prompt.

### <span id="anchor-457"></span>The "About" Option

A, Ax When this option is selected, the user sees information about the
file, including:

-   the date and time it was first uploaded
-   the date and time it was last downloaded
-   the type of computer it's for

  (If a C128 user views a file meant for the C64, they are told it is
for the C128 in 64 mode.)

  \* approximate download time

  \* if any user-submitted comments exist for the file *and if so, the
first one is displayed; a quick mod by Pinacolada*.

After that information is displayed, the user is prompted with the
following options:

C Comments read/add.  *This feature *was written b*y DER DEUTSCHER.* If
the user would like to add a comment, they may.

D Download the file.  If the user has selected a multi-file transfer
protocol, this adds the file to the download queue.  (fixme: correct?)

N Move to the next file in the directory; if they are on the last file,
they wrap around to the first file.

L Move to the previous file in the directory; if they are on the first
file, they wrap around to the last file.

M E-mail the file uploader.

R Read any file, whether SEQuential or PRoGram.

-   A program with a hexadecimal load addresses of:

    -   \$0401 (CBM PET)
    -   \$0801 (The Commodore 64's BASIC 2.0)
    -   \$C101
    -   \$4001 (The Commodore 128's BASIC 7.0 (fixme))

  display the program just as if LISTed with that computer's respective
version of BASIC.

-   You can also opt to display "control characters" such as clear/home,
    delete, or color codes in quotes in an expanded,
    easy-to-read format.
-   A program with any other load address (or a BASIC "head" and machine
    language "tail") produces a "hex dump" like a machine language
    monitor would:

**
==

<span id="anchor-458"></span>*MMMM  HH HH HH HH HH HH HH HH  PPPPPPPP*
======================================================================

**
==

<span id="anchor-459"></span>*MMMM*: Memory address
===================================================

> *HH*: Hex value of each byte

> *PPPPPPPP*: PETSCII code of each byte

**Discovered recently: This also works in 80 columns!**

-   As previously mentioned in the setup of the U/D system, credits can
    be charged for reading programs online by setting the variable *yy%*
    to the number of credits you want subtracted per block read.

For users with maintenance access:

----------------------------------

U Unvalidate a file, taking back credit for the upload.

V Validate new uploads.

For the user who uploaded the file:

-----------------------------------

E Edit the file (computer it's for, and filename)

All commands selected here, including Download, return you to the same
file in the listing you were on before selecting the command.

Hitting RETURN (or any key not listed/not applicable to the user) aborts
the About function.

<span id="anchor-460"></span>SCANNING FILES
===========================================

<span id="anchor-461"></span>S Scan files normally
==================================================

This has been enhanced to use both 40- and 80-column screens.  A normal
file scan will list files in this format:

*\#\#\# Bk’s  Dl’d  Name*

*----------------------------------------*

*001 \[200\] \[001\] “file.txt,s”*

*----------------------------------------*

From left to right, the columns represent:

<span id="anchor-462"></span>*001* The number of the listing in the directory
=============================================================================

*\[200\]* The number of Commodore 254-byte blocks (or Kilobytes if using
another computer type)

*\[001\]* The number of times the file has been downloaded

*"file.txt,s"* The filename and file type.  Unvalidated files have a
*\** in front of the name, if the user is the uploader or subop.

After all files have been selected, the total estimated download time is
displayed to the screen with a new prompt allowing you to:

\[S\]can selected files

\[D\]ownload selected files

\[C\]lear list and restart

\[K\]ill a file from the list

(All other user features are the same except having been moved into
mini-plus files to make the system easily expandable.)

SS Sorted scan

The scanned files can be sorted by:

  \* Size

  \* Number of times downloaded

  \* Alphabetically

DM Download Multiple Files

As with the D command above, this command now shows a complete
description of each file:

### <span id="anchor-463"></span>Sysop Commands

<span id="anchor-464"></span>UM Upload multiple files
=====================================================

With the Copier protocol loaded, the BBS gives you a directory of the
designated drive of the current U/D board.  You are prompted to select
either:

  \[Y\]es, \[N\]o or \[A\]bort

(This is similar to downloading multiple files in the U/X base.)

After all files have been selected, you are prompted:

"Manual or Auto descriptions?"

  \* Auto descriptions:

Asks you for one description to add it to all files selected before
writing the directory.

    \* Manual:

  Asks for a description of each file selected.

Sysop commands are now active whenever the Copier is loaded as a
protocol, not when local or psuedo-local modes are on.  In addition, if
you are logged onto the BBS from console mode, you are forced to use the
copier.  Anyone accessing the BBS as a sysop must turn on pseudo-local
mode to use the copier with the PR command.

Vx, VN The Validate or Validate New commands allow you to validate all
uploads to the current U/D library.

If the "no credit" option is active:

------------------------------------

(fixme: until validated?)

\* You may type % to award a percentage of credits to the user for
uploading the file.

\* Otherwise, the full amount of credits is added to the uploader's
account.

UM If the copier protocol is loaded, to Upload Multiple files you are
prompted for a pattern.  (RETURN defaults to \*).  You are prompted with
each filename matching the pattern, and have the ability to reply:

\[Y\]es \[N\]o \[S\]tart or \[A\]bort the upload.

When all files have been selected, you are given a list of files
selected, then an "Are You Sure?" prompt.

  \* \[Y\]es continues with the multi-upload.

  \* \[N\]o aborts.

DMJust like the Upload Multiple command, you can also Download Multiple
files from the current library to the destination drive of your choice.

ASUsers can apply for access as the subop of the current board if there
is not currently one assigned.

ACAny user with subop or remote maintenance access may add up to 500
credits to any user's account.

IDxDisplays user information just like a UL user list.  Posts,
responses, uploads and downloads are shown to subops and SIGops.

A few notes:

\* The current protocol is saved to the user's stats by using the
variable UL (which was previously used for upper/lowercase flag—not
needed but still supported in the user file).

\* Any C-64 or C-128 user who currently has this flag set to 1 will have
a default protocol of Xmodem.  Be sure to inform your users of this when
you put the system up.  Once they change their protocol to Punter, it
will remain Punter unless they change it.

<span id="anchor-465"></span><span id="anchor-466"></span><span id="anchor-465"></span>UDUpload/Download System
===============================================================================================================

This is the IMAGE BBS "file transfer base."  All users read the file
s.UD when entering the U/D section, regardless of whether they are in
"Expert Mode" or not.  (fixme: correct?)

<span id="anchor-467"></span><span id="anchor-468"></span><span id="anchor-467"></span>Moving To Another Library
----------------------------------------------------------------------------------------------------------------

<span id="anchor-469"></span><span id="anchor-470"></span><span id="anchor-469"></span>Main U/D prompt
------------------------------------------------------------------------------------------------------

<span id="anchor-471"></span>The user is shown the
==================================================

-   Total number of files in the directory
-   Number of new files uploaded since his last call
-   Total number of credit points they have
-   Current protocol in memory
-   Blocks free if in local/pseudo-local mode (fixme?)

If they are the library's subop, they are informed of this.

If a move cannot be made, they are told the requested library number
does not exist.

Typing N displays the name of the current library.

Libraries which a user can access are listed by typing L.

<span id="anchor-472"></span><span id="anchor-473"></span><span id="anchor-472"></span>Changing protocols
---------------------------------------------------------------------------------------------------------

New Punter, Slow Punter (for noisy telephone lines) and Xmodem-CRC/1K
protocols are available for use with IMAGE BBS.  Commodore 64/128 and
Amiga users default to Punter; all others use Xmodem.

\[I have no idea what Starlink is, but I'm including this info anyway:\]

"Slow Punter" has relaxed timing that works very well with Starlink. If
your BBS is reachable by Starlink, people will be able to use the "Slow
Punter" for file transfer, or you can use it to call boards using
Starlink.

(NOTE: These protocols have been updated for IMAGE v1.2a, and are very
efficient.  We think you'll be very happy with them.)

<span id="anchor-474"></span><span id="anchor-475"></span><span id="anchor-474"></span>Single file upload
---------------------------------------------------------------------------------------------------------

Each library allows a maximum of 60 files.  The user is asked for
information describing the file, which is saved along with their handle,
ID number, and the current date and time.  They receive credit points at
the ratio of whatever his access group or flag allows per block
uploaded.

There is also an option to add a file comment, used to describe what the
file is for.  Other users can view this comment, and add their own.

<span id="anchor-476"></span><span id="anchor-477"></span><span id="anchor-476"></span>Multi File Upload
--------------------------------------------------------------------------------------------------------

(The user must be using the Multi-Punter protocol.)  The BBS prompts:

***Go to multi-send mode!***

The BBS records filenames as they are received, entering them into the
directory, along with the:

-   Uploader's handle
-   BBS ID number
-   Current date and time
-   A description which says "Multi-Upload" (fixme: wasn't
    this changed?)

Users may edit the entry to provide descriptions.  Credit is given just
as with a single file upload.

(NOTE: Occasionally, noise on the phone line will cause multi-uploaded
file titles to be corrupted.  While impossible to prevent, it is a rare
occurrence, and should not cause much trouble.  You could just use the E
option afterward to edit the filename.)

<span id="anchor-478"></span><span id="anchor-479"></span><span id="anchor-478"></span>D, Dx Single File Download
-----------------------------------------------------------------------------------------------------------------

<span id="anchor-480"></span>Type D followed by the file number, from the main U/D prompt
=========================================================================================

Type D at the "About" prompt.

Note that a user can download a file if:

The files downloaded that call are less than the number of files allowed
per call, as dictated by their access group settings, unless the user's
status includes unlimited downloads per call.

The time remaining is sufficient (to begin with; errors causing delays
during transfers are ignored, since they can't be known in advance).

They must have at least as many credit points as the number of blocks
that the file contains, unless their status includes unlimited downloads
(in this case, no credits are subtracted for a download).

<span id="anchor-481"></span><span id="anchor-482"></span><span id="anchor-481"></span>Multi File Downloads
-----------------------------------------------------------------------------------------------------------

The user is asked for a starting file number, then shown each file in
the directory from that file number, and prompted

******

***\[Y\]es \[N\]o \[S\]tart \[A\]bort***

Each ***\[Y\]es*** selection: the approximate download time is shown for
their baud rate.  All the requirements to add the file to the download
queue are the same as for downloading a single file.  If everything is
okay, they can continue adding files until they reach the maximum number
of files, or choose as many files as they want to.

***\[S\]tart***: The BBS shows the list of files chosen, asking them to
confirm the list. If they do so, they are given 20 seconds to go to
receive mode, and the files will be transferred.

NOTE: Users can abort any file transfer in any mode and any protocol by
sending *CTRL-X* three times: that is, holding down the *CONTROL* key
and then typing the letter X three times.

<span id="anchor-483"></span><span id="anchor-484"></span><span id="anchor-483"></span>Listing Files
----------------------------------------------------------------------------------------------------

Scanning the file directory shows:

The directory file number

Number of blocks (or kilobytes, blocks divided by four) depending on the
user's computer type)

Number of times downloaded

Filename and file type (PRG or SEQ)

Several scanning variations exist:

S, Sx ......... Scan titles from first entry, or starting from entry \#x

SA ............ Scan titles uploaded after last call date (all libraries
in current SIG)

SN ............ Scan titles uploaded after last call date (current
library only)

SS ............ Scan titles sorted by:

-   Number of blocks
-   Number of times downloaded
-   Alphabetically

SU ............ Scan for unvalidated files

Spacebar or / aborts.

### <span id="anchor-485"></span><span id="anchor-486"></span><span id="anchor-485"></span>Other Commands

A, Ax ......... About first file, or file \#x. This shows, in addition
to information displayed by the "scan" command above:

-   The uploader's user ID and handle
-   The date and time it was uploaded
-   The date and time it was last downloaded
-   The computer type it's meant for
-   Comments about the file

<span id="anchor-487"></span><span id="anchor-488"></span><span id="anchor-487"></span>Killing Files
----------------------------------------------------------------------------------------------------

A sysop, subop, or the user that uploaded the file may enter K followed
by the file number to delete it from the file directory. They are also
asked if the file should be scratched from the disk.

If they answer *No* to this prompt, an entry to the daily activity log
titled Kill: plus the filename is made.  If a printer is online, the
same notation is printed there also.  This shows a file on disk is not
in the file directory.

When a file is killed, credit points are deducted equal to the number of
points they were given when they uploaded the file.

<span id="anchor-489"></span><span id="anchor-490"></span><span id="anchor-489"></span>Editing Files
----------------------------------------------------------------------------------------------------

A sysop, subop, or the user who uploaded the file may type E followed by
the file number to change information about it.

(fixme)

<span id="anchor-491"></span><span id="anchor-492"></span><span id="anchor-491"></span>Reading a File
-----------------------------------------------------------------------------------------------------

A user may enter R followed by the number of the file to display a SEQ
or PRG file.  They may also select R when doing an "About" on a file.

(fixme: dupe)

<span id="anchor-493"></span><span id="anchor-494"></span><span id="anchor-493"></span>Validating Files
-------------------------------------------------------------------------------------------------------

Sysops, subops, and the user who uploaded the file can "see" all
unvalidated (ie, not downloaded and/or tested) files.  When downloaded
and verified to be working files, they are validated, available for
other users to download and add comments to. In the process of
downloading a file to validate, subops:

-   Will not have credit deducted
-   The download does not count against the number of downloads per day
    (if not unlimited)
-   The time remaining is not checked when subops download in their
    own libraries.

Subops or sysops validate files by typing:

-   V, Vx to validate either the first unvalidated file (or file \#x)
-   VN to validate new files since their last call
-   VA to validate all files in the library

Unvalidated files will have a leading asterisk in the filename, and show
zero for times downloaded:

\#\#\# Bk’s  Dl’d  Name

----------------------------------------

001 \[200\] \[000\] \*"file,s"

----------------------------------------

When a file is validated, the number of downloads changes to one.

A user who uploaded a file that is not yet validated has full access to
read or download it, but will *not* have the power to validate it
(unless they happen to be the library's subop).

<span id="anchor-495"></span><span id="anchor-496"></span><span id="anchor-495"></span>DxCopying Files
------------------------------------------------------------------------------------------------------

If a user is in true local mode (from the console), when they enter the
U/D subsystem, the "copier" protocol is loaded.  To copy a file, type Dx
(where x is the file number).  The BBS tells them the approximate copy
time, allowing a filename change, or to be copied to a different
device/drive.

If no destination device is specified, it defaults to one number higher
than the source device.  (NOTE: Any device may be the target device, but
this function will ONLY copy files to drive \#0.)

<span id="anchor-497"></span><span id="anchor-498"></span><span id="anchor-497"></span>MxMoving Files
-----------------------------------------------------------------------------------------------------

If a user is in local or pseudo-local mode, type M and the file number.
They are prompted for the new directory to move the file to.

  \* L lists all available boards.

  \* If the directory is to a different device/drive, the file is copied
to that device/drive, otherwise only the directory entry is moved.

  \* If the file is moved, an option is given to scratch the file from
its source device/drive after the move is completed.

<span id="anchor-499"></span><span id="anchor-500"></span><span id="anchor-499"></span>UXFull Disk Exchange
===========================================================================================================

Full disk exchange operates very similarly to the U/D section, except
files are not placed in directories, but directly read from the device
itself (a floppy drive, for example).

UX is sub-divided into libraries just as UD is.  Each can have its own
subop, entry file, access and configuration.  Multi upload and download
functions the same as in the UD section.

Users may enter UX at most prompts to enter the full disk exchange area.

The file s.UX will be read regardless of Expert Mode status. (fixme:
correct?)

<span id="anchor-501"></span><span id="anchor-502"></span><span id="anchor-501"></span>\$, SListing Files
---------------------------------------------------------------------------------------------------------

A listing of files may be obtained by entering \$ or S. The user is
prompted for a pattern (if none is given, the default is \* for all
files).

<span id="anchor-503"></span><span id="anchor-504"></span><span id="anchor-503"></span>Free UD/UX Library
---------------------------------------------------------------------------------------------------------

While defining libraries using the +.reledit program, you may specify
any of your libraries in the U/D or U/X to be FREE libraries; that is,
no credit is deducted from the user when he downloads from these areas.
To specify a FREE board, use the +.reledit program or the Z command for
local maintenance.

In a FREE download board, the number of files per call and credit points
are not checked prior to starting a download.

<span id="anchor-505"></span><span id="anchor-506"></span><span id="anchor-505"></span>EMElectronic Mail Subsystem
==================================================================================================================

This is IMAGE BBS's private mail section.  If a user has access to this
section, on logon they will be informed if they have mail waiting, and
given the option to enter the e-mail subsystem at this time.  Upon
entering the mail system, they are told how many messages they have
waiting.

A user may also enter the e-mail subsystem by entering *EM* at any major
prompt.  The prompt for this section is "E-Mail: ".

L, LxListing E-mail

To obtain a list of the e-mail a user has waiting in the order they were
received, type L (or L followed by a number to begin listing at a
specific message) at the "E-Mail: " prompt.  This lists all messages,
reporting

-   Handle of the sender
-   Date and time it was sent
-   Message subject

<span id="anchor-507"></span>Rx READING E-MAIL
==============================================

Press RETURN to begin reading (or read the next message in a series).

Once the last message is read, they are told "No more mail."

To read a specific message, type R and that message's number.

To read all messages, type A.  All messages are displayed in succession.

Typing N reads any new messages since their last call.

<span id="anchor-508"></span>RESPONDING TO A MESSAGE
====================================================

This replies privately to the user who sent the message being read.
After reading a message, the user is presented with several options:

"Reply to &lt;sender's handle&gt;: "

  \* \[Y\]es:

    This replies to the author.

(fixme)

To respond to a specific message from the list of messages received, a
user may type R followed by the number of the message to respond to.

<span id="anchor-509"></span>S SENDING PRIVATE E-MAIL
=====================================================

The BBS prompts for the handle or user ID number who will receive this
message.  If the ID number is entered, the user log is searched, and the
handle (if found) is shown.  The sender confirms this is the

user they intended to send the message to, and are placed in the BBS
text editor.

<span id="anchor-510"></span>D DELETING E-MAIL FILES
====================================================

(This option also appears when they leave the e-mail subsystem, if there
are messages left in their mailbox.  This encourages users to keep their
mailboxes tidy and not use un-necessary disk space.)

When a user deletes their e-mail, they get the following prompt:

  Delete \[A\]ll, \[S\]ome or \[N\]one of your mail?

  \* \[A\]ll

Deletes every message held in their mailbox, after confirming an "Are
you sure" prompt with \[Y\]es.

  \* \[N\]one

Keeps every message held in their mailbox.

  \* \[S\]ome

Goes through all messages in the user's mailbox, prompting them:

  \[D\]elete, \[K\]eep, \[R\]ead, \[F\]ile away:

  \* \[D\]elete Exactly as described above.

  \* \[K\]eep Holds the message in the user's mailbox.

  \* \[R\]ead Views the message to help decide whether they wish to keep
or delete it.

  \* \[F\]ile away Removes the message from the user's mailbox, but
places it in a separate file on the e-mail disk.  These stored messages
can be later accessed with the FR (File Retrieval) command at the e-mail
prompt.

<span id="anchor-511"></span><span id="anchor-512"></span><span id="anchor-511"></span>FRPersonal File Storage
--------------------------------------------------------------------------------------------------------------

Using this command, users can

-   Read previously "filed away" e-mail messages
-   Get a directory of their personal e-mail files with \$
-   (fixme) is there a delete option?

<span id="anchor-513"></span>VVerifying E-Mail
==============================================

Type V (and the user's handle when prompted) to see how many e-mail
messages they have, and how many are from you.

<span id="anchor-514"></span>VEEditing E-Mail
=============================================

Type VE (and the user's handle when prompted) to edit any e-mail you
have already sent to that user.

<span id="anchor-515"></span>FMForced E-Mail
============================================

A user with remote maintenance access may send "forced e-mail," that is,
e-mail which is displayed to a user when they log on to the BBS.  It is
unabortable, and cannot be deleted by the user.

The user creating this e-mail is asked whether they want to create or
remove a "forced e-mail" file, and prompted for the user's handle the
forced e-mail is for.

When reading a forced e-mail file, if either of the last two lines
contain the single word

`ERASE`, the forced e-mail file is erased.

`OFF`, the user is logged off immediately after reading the forced e-mail.

Note that `ERASE` and/or `OFF` must both be entered with all capital
letters.

<span id="anchor-516"></span><span id="anchor-517"></span><span id="anchor-516"></span>QLeaving the E-Mail Subsystem
--------------------------------------------------------------------------------------------------------------------

Type `Q` or a command that takes you to any other subsystem.

If the user has any messages left in their e-mail inbox, they are
prompted whether they want to delete them.

<span id="anchor-518"></span><span id="anchor-519"></span><span id="anchor-518"></span>News Files Subsystem
===========================================================================================================

The news files are structurally different from the other file areas of
the BBS—such as Movie Files or Program Files—and for that reason they
are covered separately here.

Typing `NF` at most prompts takes you to the News File library. Here,
users can re-read BBS news files they see at login, and you can write
new ones.

If you have "File Maint Access" you will be placed in `News-Maint:`
Otherwise, the prompt users see is `News:`.

<span id="anchor-520"></span><span id="anchor-521"></span><span id="anchor-520"></span>AAdding a News Item
----------------------------------------------------------------------------------------------------------

To add a file to a directory, you are asked for the title.  This is what
the user will see when they list news items; it also names the file on
disk where the news text is stored.

If the filename begins with a `\$` (dollar sign), it becomes a "repeating"
news file, shown to users each time they log on to the BBS.

All News files are non-abortable the first time they are shown to a
user.

<span id="anchor-522"></span><span id="anchor-523"></span><span id="anchor-522"></span>Reading News
---------------------------------------------------------------------------------------------------

<span id="anchor-524"></span>Type the number of a news file (see List) to read that item.

<span id="anchor-525"></span><span id="anchor-526"></span><span id="anchor-525"></span>KxKilling a News File
------------------------------------------------------------------------------------------------------------

A maintenance operation, type K followed by the number of the news file
you wish to kill.  (fixme: confirmation?)

E*x* EDITING A FILE

If you have maintenance access, type `E` followed by the number of the
entry to edit.  You may then change the information you entered using A:
(fixme: news file name, whether it's a repeating news item) and the file
will be loaded into the editor for editing. When the file is re-saved,
you are given the opportunity to update the date of the file so it again
appears as a new file.

L_x_ LISTING NEWS FILES
_x_
Type L or Lx (x is the starting number to list from) at the prompt to
list all news files available to that access level.  Each is given a
number, and if you have News-Maint access, you can also see access
information for that file.

<span id="anchor-527"></span>**Q** LEAVING
==========================================

Entering Q will return a user to the main command level.  A user may
also go to any other section of the board by entering the appropriate
command.

<span id="anchor-528"></span><span id="anchor-529"></span><span id="anchor-528"></span>The File Libraries (Movie, Plus, RLE, Text)
==================================================================================================================================

There are three sections of the IMAGE BBS that provide very different
functions but the sections themselves are functionally identical.  They
use the same routines and all of the same commands.

<span id="anchor-530"></span>Explanation of Subsystems
------------------------------------------------------

There are four separate types of files handled by the same program:

-   Movie files Files containing cursor movement, color, and
    uppercase/graphics characters, displayed if the user is in Commodore
    C/G mode).
-   Plus files Sysops can add games or BBS utilities in this section.
-   Text files Plain Commodore PETSCII or ASCII text files.
-   RLE files Short for "Run-Length Encoded," this is a black-and-white
    high-resolution file format which requires certain
    telecommunications or viewer programs.  Graphics data is represented
    by ASCII text. Control sequences begin and end the file, telling the
    terminal or viewer to switch into or out of high-resolution modes.

We describe the Movie File Library here, but the same principles apply
to other libraries.

<span id="anchor-531"></span>MF Movie File Library
--------------------------------------------------

Type this at any prompt to enter the Movie-File library.

If you have "File Maint Access," you are placed in "Movie-Maint 1".

Since the Movie File libraries may have sub-directories and
sub-directories under those sub-directories, the number following the
prompt refers to the directory level you are at.  When you first enter
the Movie Files section, you are placed in directory level 1.

<span id="anchor-532"></span>Adding Sub-Directories
---------------------------------------------------

To add a sub-directory, you must have Movie-File Maint access.  Select A
at the "Movie-Maint" prompt.

  \* You are asked for the Title.

This is the title the user sees when listing the directory.  It has no
relation to the actual filename about to be created.

  \* Next, you are asked for the filename.

o To create a directory, type "d." followed by the sub-directory
filename you want to have on the Directory disk.

     For example, if you enter "d.movies", the BBS adds "m." to the
name, and the sub-directory is saved as "d.m.movies".

   The letter added depends on the subsystem used:

   m. movie files

   p. plus files

   r. RLE files

   t. text files

-   Next, enter the access level(s) which see that sub-directory when
    listing the files available.  Access is determined in the usual way;
    either from the chart shown earlier, or by typing "?" and answering
    Y or N for each group.
-   Finally, you are asked for how many credits to charge users to enter
    this sub-directory.  You can charge credits for:

    -   entering the sub-directory, but make accessing the files free
    -   viewing the files within, but not entering the directory itself
    -   both entering the sub-directory and viewing the files within

Or you need charge nothing if you wish.  It's up to you! The credits
charged here are put into the BBS-wide credit pool.  Refer to section
... to learn how to set that up.

### <span id="anchor-533"></span>Adding a File

To add a file to a directory or sub-directory, enter the directory or
sub- directory where you wish to add the file, type A at the prompt.

Here is a discussion of the following prompts:

  \* Title: As above.  Again, this is just what the user sees, and has
no relation to the actual filename viewed when the item is selected.

  \* Filename: Type the filename as it appears on disk.  (In the
PlusFile area, there is no need to type the leading "+.", the program
adds that automatically.)

  \* Device: Type the device number where the item can be found.

  \* Drive: Type the drive number where the file can be found.

If you do not have a dual drive (or the file is not on a dual drive),
just press RETURN.

  \* Access: Type the access level you will allow to view this file.
(Remember, you can enter a ? at the access   prompt to let the BBS help
calculate it.)

  \* Credits: Type the number of credits (if any) you will charge users
for viewing this file.

<span id="anchor-534"></span>xEntering a Sub-Directory/Running a File
---------------------------------------------------------------------

Type the number (see LIST) of a file to read/run it, or sub-directory to
enter it.

If you wish to go back one level when in a sub-directory (for example:
you are at "Movie-Maint 2" and wish to return to "Movie-Maint 1"), type
B or "&lt;" at the prompt.

Type M to return you to "Movie-Maint 1" (the Main Directory) from any
sub-directory level.

<span id="anchor-535"></span>KxKilling a File/Sub-Directory
-----------------------------------------------------------

A maintenance only operation, type K followed by the number of the file
or sub-directory you wish to kill.  You will also have the option of
scratching the file referenced by the directory entry off the disk.
Killing a sub-directory is not possible if there are files present in
that directory.

<span id="anchor-536"></span>ExEditing a File/Sub-Directory
-----------------------------------------------------------

If you are have Movie-Maint access, type E and the number of the entry
to edit.  You can change any of the information you entered originally.

<span id="anchor-537"></span>LList
----------------------------------

Typing L lists all files and/or sub-directories available at that
level.  Each is listed by number.  If you have "File-Maint" access, you
can see the filename, access, credit, device and drive information for
that file or sub-directory.

<span id="anchor-538"></span>QLQuickList
----------------------------------------

This lists the items in the directory like List does, but

<span id="anchor-539"></span>QLeaving
-------------------------------------

To leave the file areas, Q takes users to the main command level, or
type a command taking you to any other area of the BBS.

<span id="anchor-540"></span><span id="anchor-541"></span><span id="anchor-540"></span>BBBBS Database Subsystem
===============================================================================================================

This takes users to a bulletin board listing program that allows users
to add, list, or delete the numbers for other bulletin board systems.

When first entering the system they are presented with a menu of options
and arrive at the BBS database prompt ***dBASE:***

<span id="anchor-542"></span><span id="anchor-543"></span><span id="anchor-542"></span>Commands
-----------------------------------------------------------------------------------------------

The active commands for this module are:

    L)ist BBS Numbers

    Q)uit To Main Menu

    D)isplay Notes

    A)dd A Number

    R)emove An Entry

    E)dit An Entry

The last three options only appear if the user has post and respond
capabilities.

### <span id="anchor-544"></span>LListing a Number

This brings up another menu of options which allow users to narrow down
the scope of the listing they would like:

  ------------------- ------------------------------------------------------------------------------------------------------------
  ------------------- ------------------------------------------------------------------------------------------------------------

Table : Bulletin board listing options

The spacebar or / key aborts any of the listings.

### <span id="anchor-545"></span>AAdding a Number

Typing this at the *dBASE* prompt allows users with post/respond
capabilities to add a BBS number to the listing.  They are prompted for
the complete information on the board they wish to add, including

-   The BBS name
-   Phone number
-   Baud rate
-   Hours of operation

Several characteristics of the BBS are asked about (and listed when a
user lists that BBS):

-   -   If it charges a fee
    -   Has U/D areas
    -   Has online dating, games or role-playing games
    -   Is PC Pursuitable, networked, etc.

The database is checked for a duplicate under this phone number.  If
there is one, the user is notified, and returned to the *dBase* prompt.

After all prompts have been answered, the results are shown, and they
can

-   change any answers they've given
-   continue and write the entry to the database
-   or abort back to the *dBASE* prompt

Adding an entry first uses any previously deleted entries, otherwise
adds to the end of the list.

### <span id="anchor-546"></span>RRemoving An Entry

Only the sysop, a user with maintenance access, or the user that posted
a number may remove it.  Anyone else attempting to remove a number is
told the entry can only be removed by the original poster.

<span id="anchor-547"></span>A BBS name is prompted for.  The list will be searched and if the entry was posted by the same user, it will be deleted.
=====================================================================================================================================================

### <span id="anchor-548"></span>EEditing Information

A sysop or the user who posted a BBS number may edit the information.
The program asks for the entry number to edit, checking to make sure the
user has access.  If so, they may change any information in the entry,
and re-file it.

### <span id="anchor-549"></span>DDisplay Notes

This brings up a listing of abbreviations used in the BBS listings.
These include CBM for Commodore, etc.

### <span id="anchor-550"></span>QAll Done

<span id="anchor-551"></span>To leave the BBS Lister, type Q (which takes users to the main command level), or a command taking you to any other area of the BBS.
=================================================================================================================================================================

<span id="anchor-552"></span>VB VOTING BOOTH
============================================

This takes you to the Voting Booth.  If you have Remote Maint Access,

you see the prompt "Vote-Maint-&gt;", otherwise you will see
"Vote-&gt;".

If there are no topics available and you do not have Vote-Maint access,

you are returned to the main command level.

<span id="anchor-553"></span>A ADD A TOPIC
==========================================

Only available in Vote-Maint.  This allows you to add a new vote topic.

An explanation of the prompts:

  \* Subject: Enter a short but descriptive title of the vote topic.

  \* Access: Enter the access level this topic may be seen by.  This

    is set as with other areas of the BBS.

Now you are placed in the IMAGE text editor.  Type the question text.

(Do not include the answers, these are entered separately after you save

the question text.)  When done, enter .S on the first column to save

the text and continue to the next section.

<span id="anchor-554"></span>Now enter the choices a user has for this topic, and a short amount of
===================================================================================================

text which better describes this option.

<span id="anchor-555"></span>There is a limit of 9 choices, after which the voting booth
========================================================================================

automatically saves the topic.  If you have fewer choices, hit RETURN

at the last one, and you save the choices then.

<span id="anchor-556"></span>Kx KILL A TOPIC
============================================

This function is only available to users with Vote-Maint access.  Type

K and the topic number (see LIST below) to be killed.  You are asked

to verify killing the topic.  If you answer Y, the topic is killed

from the Voting Booth topic directory, and erased from the disk.

<span id="anchor-557"></span>VOTE/VIEW RESULTS
==============================================

<span id="anchor-558"></span>Available to all users, typing the topic number allows you to vote on
==================================================================================================

it (if you have not yet voted on that topic) and/or view the results.

The voting booth uses ID numbers and handles to keep track of who

voted, so a user cannot vote twice on the same topic.

<span id="anchor-559"></span>L LIST TOPICS
==========================================

<span id="anchor-560"></span>Available to all users, this lists all topics available to that user's
===================================================================================================

access level and the date each topic was created.

<span id="anchor-561"></span>If you have Vote-Maint access, the access level for each topic is also
===================================================================================================

listed.

<span id="anchor-562"></span>LEAVING
====================================

<span id="anchor-563"></span>Users may leave the voting area by typing Q to return to the main
==============================================================================================

command level, or type a command which takes them to any other area

of the BBS.

<span id="anchor-564"></span>UL USER LIST
=========================================

<span id="anchor-565"></span>Available to those who have their User List flag set, this lists
=============================================================================================

either all users, or a subset of users according to specific attributes.

<span id="anchor-566"></span>Q QUICK LISTING
============================================

A "quick list" displays the user list sorted one of two ways:

<span id="anchor-567"></span>Numerically
========================================

Alphabetically

<span id="anchor-568"></span>This list shows you only the handle and ID numbers.  You can start
===============================================================================================

listing at any number or alphabetic character(s) depending on the

type of sort you select.

<span id="anchor-569"></span>R REGULAR LISTING
==============================================

<span id="anchor-570"></span>To search for a particular user or attribute (or if you want more
==============================================================================================

information than just the handle and ID), use this option.

<span id="anchor-571"></span>Type the number of attribute(s) to search for, then fill in the
============================================================================================

information to narrow down the search.

<span id="anchor-572"></span>When you are done, or if you wish to list all users, hit RETURN.
=============================================================================================

<span id="anchor-573"></span>Next, type the number to start the listing from.  The program continues
====================================================================================================

from that point to the end of the user file.

<span id="anchor-574"></span>The space bar or slash key aborts the list at any time.
====================================================================================

<span id="anchor-575"></span>If a user has remote maintenance access, the list shows all information
====================================================================================================

about a user:

handle

ID number

last call date

computer type

area code and phone number

access group

real name

Otherwise, the list only shows:

handle

ID number

last call date

computer type

area code

<span id="anchor-576"></span><span id="anchor-577"></span><span id="anchor-576"></span>QLeaving
-----------------------------------------------------------------------------------------------

To leave the user list, type Q or hit RETURN (which takes users to the
main command level), or a command taking you to any other area of the
BBS.

See the section on
[header identifiers](#header-identifiers-in-html-latex-and-context).

The IMAGE Text Editor(#the-image-text-editor)
=====================

The text editor is where any messages on the BBS will be entered.  It
works by letting users type anything they want to type.

This is a line-based editor; you cannot use cursor keys to move up and
down a line like you can in most modern text editors/word processors.

<span id="anchor-581"></span><span id="anchor-582"></span><span id="anchor-581"></span>Entering Text
----------------------------------------------------------------------------------------------------

Simply type it into the editor.  There is no need to press *RETURN* at
the end of each line; the editor "wraps" words, so they aren't chopped
in half.

When you reach the end of the text buffer, or if you type a *.* at the
first column, you will be automatically put into *Command Mode* (see
below).

As the sysop, you can define how many lines of text (in multiples of
ten) a user can type into the editor.  (See**, page , for more
information.)  If a user is in local or pseudo-local mode, they are
allowed 253 lines in the editor.

The amount of free memory is kept track of. If this amount becomes too
small (less than 256 bytes), the message ***\*\*\* End Of Memory \*\*\*
***appears, and you must use *.S* to save, or *.A* to abort.

Entering the editor in local or pseudo-local also mode reports how many
bytes are free.

<span id="anchor-583"></span><span id="anchor-584"></span><span id="anchor-583"></span>Editor Commands
------------------------------------------------------------------------------------------------------

### <span id="anchor-585"></span><span id="anchor-586"></span><span id="anchor-585"></span>Dot Commands

Type a *.* (period) as the first character on a line.  This displays
***Command:*** and waits for you to press another key (called a “dot
command”).  This is Command Mode.

-   If you press *Delete* or *Return* keys, the `Command:` prompt is
    removed, and you are returned to the editor.
-   If you press an unrecognized command key, the editor exits to BASIC
    to check if you have added that command before assuming it is an
    illegal command.  (The `+.WF` program uses this technique
    extensively.  The "put", "get", and "view directory" commands in
    `im` also use it.  If you wish to program your own commands, we
    suggest you examine these files to see how it is done.  No
    documentation is available for this as yet.)

If you press a key corresponding to a command, the editor displays the
command, waiting for you to either:

-   enter a line range (or another character, for some commands). You
    can tell when a command accepts a line range because the cursor ends up one
    space to the right of a command.
-   or press `Return` to accept the command.

### <span id="anchor-587"></span><span id="anchor-588"></span><span id="anchor-587"></span>Line Ranges

Most commands allow a line range to be entered after the command, just
like BASIC's `list` command.  A line range can be specified in one of
the following ways:

Specifier     Meaning
---------     -------
        x     Just line \#x
       x-     From line \#x to the end of the message
      x-y     From lines \#x to \#y
       -y     From lines \#1 to line \#y

Any delimiter (comma, etc.) may be used in place of the `-`, depending on
your preference.

The commands available in the editor are grouped into related commands,
and discussed here.

### <span id="anchor-589"></span><span id="anchor-590"></span><span id="anchor-589"></span>Exiting The Editor

There are two ways to get out of the editor:

-   The first way is to abort the message you were typing, with the
    `.A`bort command.  *There is no confirmation, unfortunately.*
-   The second way is to save the message with the `.S`ave
    Text command.
-   Neither command requires or allows line ranges.

### <span id="anchor-591"></span><span id="anchor-592"></span><span id="anchor-591"></span>Reading What You Have Typed

There are several options to view the text you have already typed:

-   First, the `.R`ead command.  This displays each line just as it
    was typed.  Each color change character and MCI command is shown
    without being acted upon. This might be useful to "proofread" your message.
-   Next, the `.M`CI Read command.  This interprets MCI commands, and
    displays color change codes.
-   Finally, you can also `.L`ist the text, which displays line numbers
    (used in line ranges for other commands), plus behaving like `.R`ead.

If no line range is given for the `.R`ead, `.M`CI Read or `.L`ist
commands, all text in the buffer is read or listed.

You can pause text with *Ctrl-S* or *Home* keys at any time.  Messages may
be aborted while paused with the spacebar or `/` keys.

### <span id="anchor-593"></span><span id="anchor-594"></span><span id="anchor-593"></span>Manipulating Text

`.D`elete removes lines of text from your message permanently; there is no
"undo" capability.

-   Any line range you type after .Delete is removed from the buffer.
-   If no line range is specified, the last line of text is deleted.

<!-- comment: bla -->

-   `.E`dit changes lines of text.  When a line is edited this way, the
    line number is displayed, then the text itself, just like the `.L`ist
    command does.  You may then type the new line below it.  (See
    “[Control Keys](#anchor-595)” for useful editing keystrokes.)
-   Pressing *Delete* or *Return* as the first character on the line causes
    the editor responds with `(No Change.)` and returns to allowing text entry.
-   Typing `.` as the first character causes `Command: Exit` to appear and
    abort the Edit command, once again allowing text entry.
-   If no line range is specified, `.E`dit defaults to the last line of
    text entered.

### <span id="anchor-596"></span><span id="anchor-597"></span><span id="anchor-596"></span>Editor Modes

## Insert Mode
The `.I`nsert command enters Insert Mode.  Any line number you specify after
`.I` is where you start inserting lines.  If no line number is specified,
line \#1 is assumed.

When you are in Insert mode, it is shown by displaying *Ix:*, where *x* is
the line number you are inserting at.

As you type each line of text, text on subsequent lines is moved down in
the buffer, then your line is put in its place.

You can exit Insert Mode by typing a `.` as the first character on the
line.  This responds with *Command: Exit* and goes back to the normal
editor.

## Line Numbering Mode
The `.O` command toggles Line Numbering Mode on or off.  This mode, when
on, displays line numbers as you type text.

### <span id="anchor-598"></span><span id="anchor-599"></span><span id="anchor-598"></span>Shaping Your Text

The `.J`ustify command allows you to format your text in one of 7
different ways.  After typing the J command, you are prompted:

`Justify (C,E,I,P,L,R,U): `

**

These are the seven Justify commands.  Press the key corresponding to
which justification mode you want, or to escape, type (fixme: period?)
*Delete* or *Return*.

If a valid command is selected, the editor displays the command name,
and then allows you to enter a line range.

If you do not specify a line range, the Justify commands default to all
text in the buffer.

The Justify commands are:

  ----------- -------------------------------------------------------------------------
  ----------- -------------------------------------------------------------------------

Table : Text editor justification commands

The *.B*order command puts a border around your text. If you do not
specify a line range, it will default to all text entered. If there is
not enough room on a particular line to add both border characters, that
line is ignored.

**Tip: Set the *.C*olumns width to 2-4 characters less than your current
line width before typing the text to be bordered.**

The *.C*olumns command **followed by a two-digit number between 22 and
80** changes the number of characters the editor allows you to type on a
line *before wrapping overly-long lines to the next line* between 22
**columns (f*or VIC-20s*)** and 80.

If you do not specify a column width after the command, the current
column width is displayed.

A related command is *.\#*—this displays a 40-column scale for manually
centering text, among other purposes.  There is no prompt for a line
range; the scale gets displayed as soon as you hit \#.

### <span id="anchor-600"></span><span id="anchor-601"></span><span id="anchor-600"></span>Starting Over

The *.N*ew (Clear Text) command re-starts the editor, erasing all text
you have typed.  *There is no confirmation, unfortunately, something I
plan on remedying in Image BBS 2.0!*

### <span id="anchor-602"></span><span id="anchor-603"></span><span id="anchor-602"></span>Searching For Text

The *.F*ind command allows you to search for any occurrence of a
character, word or phrase.  If no line range is entered, all text will
be searched.  Find will prompt you for the text to search for, and will
list all occurrences of it.

### <span id="anchor-604"></span><span id="anchor-605"></span><span id="anchor-604"></span>Replacing Text

The *.K* (Replace) command will prompt you for an optional line range,
then a ***Search Phrase:*** as *.F*ind does, but also ask what phrase
you want to replace it with.  Then it will go through the text.  If the
replacement phrase is too large to fit within the current line length,
the editor will display ***Too big, can't fit.*** and skip that line.

### <span id="anchor-606"></span><span id="anchor-607"></span><span id="anchor-606"></span>Disk Access

(These commands are available from local/pseudo-local mode only.)  The
`.G`et and `.P`ut commands allow you to load a file from, edit using all the
normal editing facilities, then save that file to any device and drive,
rename it, etc., and resave them to the same device/drive, or a
different device/drive if desired.

*fixme* Rewrite:

(These commands are only available from local or pseudo-local mode.)

`.Get` allows you to load a text file from any device and drive. It
appends the file to any text already in the editor's buffer.

You can then use all the normal editing facilities.

> A suggestion: if you are trying to work with SEQ files with C/G codes
> in them, use `.Columns 80` first, so lines don't word-wrap.

`.Put` allows you to save the text file in the buffer to a specified
device and drive. If the specified filename already exists, you can
either replace the file or append the text in the buffer to the existing
file.

`.$` (View Directory) command views a disk directory of any device and
drive, with a pattern if desired.

`.&` reads an existing file. A filename, device and drive are prompted
for.

`.!` issues a DOS command. If a “new” (`n0:diskname,id`) or “scratch” (`s0:filename`) command is issued, you
are prompted to confirm your actions.

### <span id="anchor-608"></span><span id="anchor-609"></span><span id="anchor-608"></span>Getting Help

Type `.?` or `.H` to read a condensed version of this manual section.

### <span id="anchor-610"></span><span id="anchor-611"></span><span id="anchor-610"></span><span id="anchor-595"></span><span id="anchor-610"></span><span id="anchor-611"></span><span id="anchor-610"></span>Control Keys

Certain key combinations are used to edit your text while you are typing
it, whether in the BBS editor or at a BBS prompt.  For example, any
character that you delete with the *Delete* key can be “re-typed” with
*Ctrl-U*.  Other control keys:

  Right     Left     Center     Default
-------     ------ ----------   -------
     12     12        12            12
    123     123       123          123
      1     1          1             1

Table: Demonstration of simple table syntax


Table: Text editor & BBS prompt control keys

### <span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span><span id="anchor-614"></span><span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span><span id="anchor-615"></span><span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span><span id="anchor-614"></span><span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span><span id="anchor-184"></span><span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span><span id="anchor-614"></span><span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span><span id="anchor-615"></span><span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span><span id="anchor-614"></span><span id="anchor-612"></span><span id="anchor-613"></span><span id="anchor-612"></span>Message Command Interpreter

The Message Command Interpreter (MCI) allows you to do a variety of
things within messages you type.  Each MCI command consists of:

-   the British pound character (£) for Commodore users, or
    backslash (\\) for other computers
-   a command letter (can be either upper- or lowercase)
-   a number or letter
-   any arguments/parameters.

Numbers must be entered in a certain way.  Since the parameter after a
command letter may only be one character, letters are substituted in
some cases, as follows:

  --- -------- ---- --------
  --- -------- ---- --------

Table : MCI numbering system

*Think of it as "extended hexadecimal."  And by the way, this next
good-sized chunk was pretty extensively reworked; I think the examples
in the original manual don't always explain themselves very well.*

*Plus, one thing to mention: If ever you need to output a British pound
sign, type two of them.  This is technically called "escaping" MCI; the
first prepares to interpret the following character as an MCI command,
the second cancels it.*

In general, MCI is what "spices up" an IMAGE BBS.  It allows you to add
color, cursor movement, and a "personal touch."  The MCI commands
available in IMAGE BBS are:

<span id="anchor-616"></span>***£AnTEXT£ About***
=================================================

Compare MCI variable £Vn to TEXT.  Notice the ending pound sign which
delimits the comparison.  (For a list of MCI variables, see the £V
command.)  The comparison result can be used with £D or £T.

*£A2SYSOP£*Compares the user's handle (*£V2*) to *SYSOP*.

<span id="anchor-617"></span>***£Bx Bells***
============================================

Send x bell characters \[CHR\$(7)\] to the user; if the user's terminal
supports bells, they hear them.

-   Tip: Speed up or slow down by using the £Sx command!

<span id="anchor-618"></span>***£Cx Color***
============================================

Set the current display color to *x*, where *x* is from the following
table:

<span id="anchor-619"></span><span id="anchor-620"></span><span
id="anchor-619"></span>

  ------- -------------- ------- -------------- ----- ---------------------
  ------- -------------- ------- -------------- ----- ---------------------

Table : MCI color codes

-   0, black, is omitted since that is usually the color choice for
    terminal backgrounds.
-   Commodore users can use *CTRL*- or *C=* *1-8* instead of *£Cx*.

<span id="anchor-621"></span>£Dx Jump if not equal
==================================================

Skips *x* lines when the result of the last compare command (£A or £T)
was *not* equal.

**Display an appropriate message based on whether the user's handle is
or is not *SYSOP*:**

*£A2SYSOP££D1*Compare user's handle to SYSOP, skip next line if not

*Hello, Sysop!£D1*Output “Hello, Sysop!”, skip next line

*Hey, you can't read this!*Output message, continue**

*£X1*Abort the file or message**

<span id="anchor-622"></span>£Ex Jump if equal
==============================================

Skip *x* lines if the result of the last compare command (£A or £T)
*was* equal.

Display a message based on whether the user's handle is USER:

*£A2USER££E1*

*Congratulations, your handle is USER!£E1*

*Too bad your handle isn't USER!*

*£X1*Abort the file or message**

<span id="anchor-623"></span>£F1 Form feed
==========================================

This command sends a "clear screen" character to the user. \[CHR\$(147)
on Commodore equipment, or CHR\$(12)--a form feed -- in ASCII mode\].

<span id="anchor-624"></span>£Gx Get character
==============================================

Wait until the user presses a key.  The keypress is stored in an\$ (MCI
variable £v7).

If x=1, only uppercase input is allowed. If x=0, both uppercase and
lowercase are allowed.

*Press a key: £G1*Prompts the user and waits for one

keypress (only uppercase input is accepted).

<span id="anchor-625"></span>£Hx Backspaces
===========================================

Display *x* backspaces/deletes (depending on the user's terminal
requirements).

*Apple£H5Banana*This displays Apple, immediately erases it with five

backspace/delete characters, then Banana

is displayed in its place.

<span id="anchor-626"></span>£Ix Line input
===========================================

Pauses output, allowing the user to input a line of text. The input is
stored in AN\$ (MCI variable £V7).

-   If x=0, the input can be in both upper- and lowercase.
-   If x=1, the input is in uppercase only.

*Enter your name: £I1*Prompts the user, then accepts input

in all uppercase characters.

*Hello, £V7!*Echo the user's input.

<span id="anchor-627"></span>£Jx Jump
=====================================

Do not display the next x lines of the message or file.

*Displayed£J1*This skips the next line.

*Not displayed*

*Displayed again*

<span id="anchor-628"></span>£Kx Kolorific mode
===============================================

Changes the color of each character output.

-   If x=0 (zero), Kolorific mode is turned off.
-   If x is any other color code (see £Cx), Kolorific mode is enabled,
    starting with £Cx.

*£K2This is a test£K0*Turn Kolorific mode on, starting with the color
red.

Displays "This is a test", then turns Kolorific mode off.

<span id="anchor-629"></span>£Lx Printer
========================================

Control the printer attached to the BBS, if online.

-   If x=0, printed output is stopped.
-   If x=1, printed output is started (or resumed).

*Note:* Printed output stops at the end of each line; you must include
£L1 on each line to be printed.

*£LlHello*Print *Hello* on the printer.

<span id="anchor-630"></span>£Nx New line
=========================================

Display *x* carriage returns.

<span id="anchor-631"></span>£Ox "Over"
=======================================

This command repeats a character 19 times.  It is useful for making
menus, etc.

Parameters: Replace x with the character wanted.

\*£0-£0-\*

Displays the following:

*\*--------------------------------------\**

<span id="anchor-632"></span>£Px Print mode
===========================================

Sometimes referred to as “cursor dancing,” print modes allow each
character output to be displayed in a variety of ways, usually to move
the cursor, or perform "special effects."  Replace x with the print mode
number.  The print mode is set back to 0 at the end of each line.

There are thirteen very powerful print modes in IMAGE BBS.  We suggest
trying to come up with interesting ways to use them -- it is possible to
create an entire “movie” file entirely within the IMAGE BBS editor with
these commands!

<span id="anchor-633"></span>*ASCII:*
=====================================

*======*

0 - normal printing

1 - character, backspace, character

2 - character, 8 spaces, 8 backspaces

3 - character, backspace

4 - space, character, 2 backspaces, character

5 - character, bell

<span id="anchor-634"></span>*COMMODORE C/G:*
=============================================

*==============*

6 - character, 2 cursor lefts (displays !drawkcab)

7 - character, cursor left, cursor up (displays up)

8 - character, cursor left, cursor down (displays down)

(fixme: add the rest, 4 diagonals)

<span id="anchor-635"></span>£Qx Reset MCI defaults
===================================================

Turns off the following features:

\* Printer mode (see £Lx)

\* Reverse mode (see £Rx)

\* Uppercase mode (see £Ux)

The current print mode (see £Px) and print speed (see £Sx) are set to 0
for normal output at the fastest speed.

Parameters: \* If x=0, then the current color is set to the default
color.

\* Otherwise, the default color and current color is set to x.

(fixme)

<span id="anchor-636"></span>£Rx Reverse mode
=============================================

Controls displaying text in normal or reverse modes.

Parameters:

 \* If x=0, reverse mode is turned off

 \* If x=1, reverse mode is turned on

Notes:

 \* Reverse mode turns off at the end of every line.

 \* Commodore users can also use CTRL-9 / CTRL-0.

<span id="anchor-637"></span>£Sx Print speed
============================================

Delay character output by a multiple of tenths of a second.

Parameters: \* x ranges from 1-J (.1 to 1 second)

<span id="anchor-638"></span>£TxTEXT£ Test variables
====================================================

Used in conjunction with £D and £E.  Compares a variable to TEXT
(similar to £A).

If x=1, tests user input (AN\$).

If x=2, tests access group (AC%).

£T29££D1Compare the user's access level to 9;

Hi, sysop! Welcome!£X1display an appropriate message.

£V2, this function is only for sysops.

<span id="anchor-639"></span>£Vx MCI variables
==============================================

Display the desired MCI variable.

Parameters: x is MCI variable number:

  ---------- --------------------- ---------- -----------------------------------
  ---------- --------------------- ---------- -----------------------------------

Table : MCI variables

<span id="anchor-640"></span>

<span id="anchor-641"></span>£Wx Wait
=====================================

Delay x seconds before proceeding, similar to £Sx.

Parameters: \* x ranges from 1-J (1 to 15 seconds)

<span id="anchor-642"></span>£X1 ........................................... Abort file
=======================================================================================

Skips the rest of the lines in a file/message, not displaying anything
contained in those lines.

\[The number of lines skipped is actually limited to 255; I discovered
this while re-writing the BBS editor help menu file.\]

<span id="anchor-643"></span>£\#x .................................... Leading characters
=========================================================================================

When you use £%v (below), this specifies either:

\* The number of digits to display

\* To use leading zeroes or spaces

Parameters: \* When x is a number \[between 1 and 5?\], x sets the
number of digits to display a numeric value with.

\* When x equals zero, as many digits are in the number are displayed.

\* When x is a space character, leading spaces are used, but the number
of digits to display is not affected.

<span id="anchor-644"></span>See the examples for £%v, below.
=============================================================

<span id="anchor-645"></span>£%v .............................. Display integer variable
========================================================================================

Display the value of any one-letter integer variable with or without
leading characters.

\[The periods in the examples are not shown in actual use of this
command; they only illustrate how many leading spaces are used.\]

Example 1: *£\#4£\# £%a* If a%=l,   this displays "...1"

Example 2: *£\#2£%a* If a%=l,   this displays "01"

If a%=23,  this displays "23"

If a%=789, this displays "89", the *rightmost* two digits.

  Example 3: £\#0£%aIf a%=l,   this displays l

If a%=42, this displays "42"

<span id="anchor-646"></span>£\$xDisplay string variable
========================================================

Display any one-letter string variable (A\$, for example).

£\$a

Display the contents of the string variable A\$.

<span id="anchor-647"></span>£←xxTab
====================================

This command tabs the cursor from the left column, to column \#xx.

Notes: \* Use the back-arrow key to the left of the 1 key.

\* To tab over less than ten columns, use a leading zero (£←05, £←08).

If the tab-to column specified is less than the column where the cursor
is now, any text after the tab command is displayed as normal.

<span id="anchor-648"></span><span id="anchor-649"></span><span id="anchor-648"></span><span id="anchor-650"></span><span id="anchor-648"></span><span id="anchor-649"></span><span id="anchor-648"></span>The <span id="anchor-316"></span><span id="anchor-648"></span><span id="anchor-649"></span><span id="anchor-648"></span><span id="anchor-650"></span><span id="anchor-648"></span><span id="anchor-649"></span><span id="anchor-648"></span>The Image Terminal Program
=================================================================================================================================================================================================================================================================================================================================================================================================================================================================================

IMAGE BBS has a built in Commodore 1670/Hayes-compatible terminal
program for dialing out to other BBSes without having to take your BBS
off-line.  It is equipped with several features, including:

-   a phone book
-   auto dialer
-   X-modem and Punter file transfer
-   full Commodore C/G capabilities

For the most part it is self-documenting, with several on-line menus to
help you.

<span id="anchor-651"></span><span id="anchor-652"></span><span id="anchor-651"></span>Using the Terminal Program
-----------------------------------------------------------------------------------------------------------------

To load and use the term program, press ← at BBS idle mode, and the term
will load and display the opening menu, along with several parameters
displayed on the top right window of the screen.  To change any of these
parameters, select the "Term Parameters" option from the main menu.

From here, you are able to change

-   ASCII/C-G mode
-   baud rate
-   U/D protocol
-   dial mode (tone or pulse)

Other options on the main menu include terminal mode, file operations,
phone book, disconnect, return to the BBS environment, and send line
break (for the MERIT system).

<span id="anchor-653"></span><span id="anchor-654"></span><span id="anchor-653"></span><span id="anchor-655"></span><span id="anchor-653"></span><span id="anchor-654"></span><span id="anchor-653"></span><span id="anchor-354"></span><span id="anchor-653"></span><span id="anchor-654"></span><span id="anchor-653"></span><span id="anchor-655"></span><span id="anchor-653"></span><span id="anchor-654"></span><span id="anchor-653"></span>The Phone Book
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Here is where you may dial numbers entered into your s.phonebook file,
or any other number that you wish.  When you choose the phone book
option from the main menu, you see the first five numbers (if you have
the file), along with "dial number not

To write this file, you should include three items of data for each BBS
you want in the phone book:

ItemExample

the name of the BBSLYON'S DEN

the phone number1-313-437-9486

the baud rate1200

\[...mising text…\]

This section will be altered after adding high-speed +.t to the mix...
but keep BBSes for historical preservation)

These should be separated by a carriage return, and can be added at any
time, Example:

<span id="anchor-656"></span>LYON'S DEN
=======================================

1-313-437-9486

1200

PORT COMMODORE

1-801-423-2734

2400

NIGHT FLIGHT

1-615-824-5488

1200

(NOTE: Make sure that the *first* line of the file contains the first
BBS name and not a carriage return, and that there are *no* extra
carriage returns before, between, or after the information, or the BBS
will not read the information in correctly.)

"next page", or "previous page".  Simply hitting return at the prompt
will take you back to the main menu.  Selecting next or previous page
will go on through the list in your phonebook.  Selecting any of the
numbers, or "Dial number not shown", and entering the number when
prompted, will then prompt you for the autodial (repeat) option.

If the autodial option is selected, it will keep track of how many tries
for that number (Press "/" to abort the autodialer).

Once a connection is made, you are put into term mode for the
connection.

To go back to the main menu, press CTRL plus the Commodore key.

<span id="anchor-657"></span><span id="anchor-658"></span><span id="anchor-657"></span>File Operations
------------------------------------------------------------------------------------------------------

You can change communication parameters or use file operation functions
here, which include:

-   getting a disk directory
-   sending a disk command
-   changing device/drive
-   read/send a SEQ file
-   upload/download functions (including multi-upload & download)

<span id="anchor-659"></span><span id="anchor-660"></span><span id="anchor-659"></span>Maintenance Functions
============================================================================================================

There are several maintenance commands available, with differing
availability:

-   only at the main prompt
-   at all prompts
-   from local or pseudo-local mode
-   to users with remote maintenance access

Each type of command is described in this chapter.  Here is a brief
synopsis of each command, followed by a more complete description.
Commands marked with \* are available only from local/pseudo local mode.

  --------- ------------------------------------------------------- ------------------------
  --------- ------------------------------------------------------- ------------------------

Table : Maintenance functions

<span id="anchor-661"></span><span id="anchor-662"></span><span id="anchor-661"></span>Local Maintenance Commands
-----------------------------------------------------------------------------------------------------------------

### <span id="anchor-173"></span><span id="anchor-663"></span><span id="anchor-173"></span><span id="anchor-664"></span><span id="anchor-173"></span><span id="anchor-663"></span><span id="anchor-173"></span>ECS<span id="anchor-185"></span><span id="anchor-173"></span><span id="anchor-663"></span><span id="anchor-173"></span><span id="anchor-664"></span><span id="anchor-173"></span><span id="anchor-663"></span><span id="anchor-173"></span>ECSExtended Command Set Editor

The Extended Command Set or ECS allows you to add or delete commands
from your BBS without the need to modify your im module or re-boot the
BBS. It also gives you flexibility in these areas:

-   enabling or disabling commands
-   password-protecting access
-   restricting availability of sysop-only commands to local or
    pseudo-local mode
-   restricting certain commands to specific security levels
-   configuring whether a command calls a plus-file module on disk or a
    specific line in the memory-resident *im* module (and whether that
    call requires a GOTO or GOSUB)

    However, it will *not* allow you to make changes to the
    BASIC program. The ECS will allow you to add both main level and all
    level commands either by loading a module or calling a
    pre-positioned line in your im module. Each command has several
    flags attached to it:

  ------------ ------------------------------------------------------------------------------------------------------------------------------------------------
  ------------ ------------------------------------------------------------------------------------------------------------------------------------------------

Table : Extended Command Set flags<span id="anchor-665"></span>Table :
Extended Command Set flags

#### <span id="anchor-666"></span>Using The ECS Editor

Using the ECS command editor is really very simple—there are just a few
things that you should know.

1.  If you Add or Edit *any* commands while you are in the editor, you
    should first (S)ave the new configuration then (M)ake it active.
2.  A pre-configured ml.ecsdefs has been included with this package that
    contains all the standard IMAGE v1.2 commands plus the commands MA
    (macro toggle) and ECS which loads the ECS editor (+.ecs).

Re-boot your BBS and add or edit any commands that you wish using +.ecs
by entering ECS at the main prompt.

NOTE: ml.ecsdefs is a ML file and must be COPIED. Also if you plan to
use the MACS (also included on this diskette) you must install the ECS
prior to installing MACS.

<span id="anchor-667"></span><span id="anchor-668"></span><span id="anchor-667"></span>EDUser Edit
--------------------------------------------------------------------------------------------------

Edit your users' information whenever needed.  Type the handle or ID
number of the user to edit.

-   If entering the ID number, do not enter the BBS identifier (if your
    identifier is *SS*, and you want to edit user number 50, you would
    enter *50*, not *SS50*)

The BBS then loads the user's stats into memory.  Anyone with
pseudo-local maintenance access may change anything they wish.

-   One exception to this is the password, which can only be seen or
    changed by the sysop (ID\#1).

The first page of user information is shown.  If you wish to change
anything, type its number at the prompt, or *N* to view the next page of
information.

Then enter the new information.  Don't worry if you make a mistake: you
can change it again if you wish, nothing is permanently changed until
you answer *Y* to the ***Save changes?*** prompt when you are done.

If the information you wish to change concerns the user's "flags”—that
is, certain functions the user can access—then you get a list like in
the BBS configuration editor (page [Error: Reference source not
found](#anchor-356)).

*No matter how much I read and re-read this next paragraph, it never
made much sense to me.  So I'm re-writing it, hopefully keeping the
spirit and intent of the original wording...  hurty head bad...*

These flags reflect the default settings whenever you first change the
access group you gave the user.  Afterwards, they may be customized on a
per-user basis.  Changing one flag will not affect any other flags for
that user.

You may also delete an account or reserve an account with this function
by changing the user's handle.

-   To delete the account, change their handle to an \^ (up arrow). The
    BBS prompts with "Delete this user?" before any action is taken.  If
    "yes" is selected, the account is considered deleted, and it is now
    available for a NEW or REServed user (although it is not
    overwritten, making it possible to "resurrect" a deleted user by
    changing the handle back, before another new user takes
    that account).

-   REServed users get prompted for a password, number of credits, and
    access level.  (More on this in the "RS" function below.)

<span id="anchor-669"></span><span id="anchor-670"></span><span id="anchor-669"></span>CPFile Copier
----------------------------------------------------------------------------------------------------

This command allows you to access the online file copier, patterned
after the popular "Copy-All" program by Jim Butterfield.  Our thanks go
to him for supplying us with the source code to help us write this
version.  The online copier will copy PRG, SEQ, and USR files from one
device or drive to another with little effort.

NOTES:  *CP* will NOT copy files to the same device and drive.  Use the
"DC" command for this, with standard Commodore DOS commands \[ex.
*C0:FILE2=FILE1*\].

CP will also not copy REL files.

*Use "+.CP-rel" online, or "Copy-All" or "rel copy" offline to do this.*

<span id="anchor-671"></span><span id="anchor-672"></span><span id="anchor-671"></span><span id="anchor-673"></span><span id="anchor-671"></span><span id="anchor-672"></span><span id="anchor-671"></span><span id="anchor-353"></span><span id="anchor-671"></span><span id="anchor-672"></span><span id="anchor-671"></span><span id="anchor-673"></span><span id="anchor-671"></span><span id="anchor-672"></span><span id="anchor-671"></span>Write File
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

You may access the IMAGE editor as a mini word-processor, to write or
edit any sequential (SEQ) file.  When you type the *WF* command at the
main prompt, the editor will load, and you are able to use it to *.P*ut
(save) and *.G*et (load) files from any device and drive you have
online. This makes it easy to write, edit, or—in the case of "putting"
to a file which already exists, append to—a file.

### <span id="anchor-674"></span><span id="anchor-675"></span><span id="anchor-674"></span><span id="anchor-676"></span><span id="anchor-674"></span><span id="anchor-675"></span><span id="anchor-674"></span>Additional Dot Commands

There are also additional editor commands built into the *WF* function
not normally available from the editor subsystem:

  ----- ----------------
  ----- ----------------

Table : WF editor dot commands

.Get

You are prompted for a filename, then the device and drive the file is
on.  The file will be loaded (assuming no errors occur) and you can edit
it as necessary or create a new file if you wish.  (fixme: correct?)

When finished, you have two choices:

.Save

Saves the file (prompting for a filename if one hasn't been established
with the Put command).  It checks for the presence of an existing file
under the given name, and if one is found, it prompts:

\[A\]ppend \[R\]eplace \[Q\]uit:

Here, you can:

-   \[A\]ppend the text in the editor to the existing file
-   \[R\]eplace the file on disk with the text in the editor
-   \[Q\]uit to the editor (keeping existing text intact) without saving
    changes

.Put

Allows you to save the file wherever you wish, returning to where you
left off in the editor to continue working.  You are prompted for a
filename in the same way as above (if you used *.G*et, the filename you
got is displayed serving as a reminder and the default filename).  You
are prompted for the device and drive to save to (the default is 8:0).

.Query

Re-displays the editor's opening message, showing how many lines used so
far, remaining, and bytes of free memory.

.Unborder

Removes a border or partial border that you have done.  It removes the
first and last lines, and first and last characters from each line *if*
they are the same character.

<span id="anchor-677"></span>RRun a Plus-File
---------------------------------------------

Run any plus file you have on your plus file disk from the main prompt.
You are prompted

Run +.

Type the filename after that.  (Pressing RETURN by itself exits to the
main command level.)

<span id="anchor-678"></span><span id="anchor-679"></span><span id="anchor-678"></span>Remote Maintenance Commands
------------------------------------------------------------------------------------------------------------------

### <span id="anchor-680"></span><span id="anchor-681"></span><span id="anchor-680"></span><span id="anchor-682"></span><span id="anchor-680"></span><span id="anchor-681"></span><span id="anchor-680"></span><span id="anchor-292"></span><span id="anchor-680"></span><span id="anchor-681"></span><span id="anchor-680"></span><span id="anchor-682"></span><span id="anchor-680"></span><span id="anchor-681"></span><span id="anchor-680"></span>VFView Feedback

Only those with remote maintenance access may use the VF function. When
first entered, it counts the number of messages which fall into the
following categories:

-   Feedback
-   Error log
-   New user log
-   Telecheck
-   Canned messages

*I'll let Fred Dart explain the operation of some features, with slight
formatting changes to the file:*

<span id="anchor-683"></span>The following article appeared in
==============================================================

the January issue of "The Reflection"

<span id="anchor-684"></span>It is reproduced here for the
==========================================================

benefit of any that may have missed

it.  It may be used as a text file

on other boards, if used in its'

entirety.

"+.VF"

By: Fred Dart (THE CHIEF)

This month we are going to look at one of the truly outstanding features
of IMAGE 1.2, the enhanced "+.VF" program.

The basic "+.VF" from the version 1.0 has been expanded and enhanced by
Dr.Bob of the "Enchanted Forest BBS" in Philadelphia.  Bob has worked
very closely with Little John and has really done a tremendous job with
the "+.VF".

Some of the new features include "canned" messages and selective
deletion of feedback, new user feedback, etc.  We'll look at all of the
different commands.

The feature that seems to cause the most questions is the "canned
message" feature.  A "canned message" is simply a pre-written message or
"form letter" that you may wish to send to a user, much like the "new
user welcome".

From the initial VF: prompt, selecting *C* will bring up an option menu
consisting of A/dd, E/dit, K/ill, L/ist, or S/end.  Selecting the Add
option will ask you for a title for the message, and then put you in the
editor to write your message.  Your message can be as brief or as long
as you'd like and can contain any MCI or color just as any message
entered in the editor.

The Edit option will ask which message to edit.  A numeric input is
required.  If you don't remember which one you want to edit, simply
entering the *?* will bring up a list of titles and numbers, enter the
number of the message you wish to edit and it will be loaded into the
editor for whatever editing you desire.

The Kill option works the same way, the number of the message you want
killed.  Better be sure here as there is no safety check: if you say
kill, it is gone.

List does just that, it will provide a list of available "canned
messages".  You can have up to 60 of them if you desire.

The final option is Send, which simply asks which one to send.  Again,
if you don't know a question mark will bring up the list.  Very neat.

When reading any of the feedback, new user feedback, telecheck log or
error log you have several other options available as well, they are:

<span id="anchor-685"></span>Accs/Can/CRed/Del/View/Fwd/Rspd/Next/Over/Quit/New \#.
===================================================================================

The ones that are new or changed include the Can/CRed/Del and View. The
others are unchanged, or have minor changes.

Selecting *C*an will give you the option of sending the user any of the
"canned messages."  You might even have one that you want to send to
people that continually have trouble with the telecheck or you might
have one that you send to anyone that runs into an error on your system
(though he should have gotten error e-mail).  When you select *C* you
will be asked "which one" and a *?* will bring up the list of those you
have available.

*CR*ed is very handy for giving credit.  I'm sure you have all had
occasion to need to restore some credit to a user for a bad download or
as a reward for something, now you can do it from here, no need to go
into ED just to give him credit.

Del is one of my own favorites.  The user that signs on with an
obviously fake account or the irate user that says "just delete me from
your system if I can't....." whatever.  The D works *wonders*... and
really feels *good* afterwards.  May not get a lot of use but when it
does it is worth having.

Finally the View.  Particularly good on systems where more than one
person may give access.  You can View the person's account to see what
his status is.  If he has been given access or if he wants some credit
or whatever, the View is particularly useful.

In addition to these great features there has also been added the
"Selective delete" option so you can delete all or any part of your
feedback or other messages.  When Delete is selected from the VF:
prompt, you select which to delete then have an option of selective or
auto delete.

*Selective delete picks which messages you want to retain through a menu
of options:*

**

*\[D\]elete \[K\]eep \[A\]bort*

**

<span id="anchor-686"></span>*The options should be self-explanatory, I hope.*
==============================================================================

**

All in all the VF is now about anything a busy sysop could want to
maintain his daily message traffic from his users.  This is really one
of the better "hidden" features of 1.2.  Well done Dr. Bob.

(A late note here, someone that just converted to IMAGE from 12.0 said
that the "+.VF" was one of the best features he had noticed since his
conversion.)

\(c) January 1990 FandF Products

<span id="anchor-687"></span>Permission to reprint is granted provided the file is printed in its entirety.
===========================================================================================================

<span id="anchor-688"></span>If the user is in "Local" or "pseudo-local" mode, they are given an option to delete the entries.
==============================================================================================================================

Entering N, E, or F will allow them to read the entries beginning with
the first entry or with any entry number he may wish to enter (Example:
if there were 10 feedback messages, they could start reading number 5 by
entering a 5 at the prompt, or enter N to begin reading those entries
that are NEW since his last call, if the feedback was not deleted
previously).

After each message he has several options, including:

-   advancing to any message by typing the message number
-   N or RETURN continues on to the next message
-   R responds to the message
-   A changes the user's access
-   F forwards the message to any other user as e-mail
-   Q quits back to the options menu

After all messages have been read, the user is returned to the options
menu.  If access is assigned to a new user the Sysop is given the option
of sending the new user a "New User Welcome" that consists of the file
s.nu welcome.  (This can be created using the WF command shown above.)

New user feedback may also be archived if desired.  This copies your new
user feedback to a file called e.nark (which could be backed up from
time to time, as many sysops like to do).  This eliminates the search
through older messages each time VF starts up.

<span id="anchor-689"></span><span id="anchor-690"></span><span id="anchor-689"></span>RSReserve Account
--------------------------------------------------------------------------------------------------------

A reserved account (an account with a pre-assigned password, number of
credits and access level) can be established using this command.  A
reserved account is useful for a new user who may sign up when you are
not available to validate them.

The RS command establishes any deleted account (where the handle is \^)
as a reserved account. When first entered, you are prompted to enter the
starting account number.

-   Typing a number starts searching at that account number
-   If E is typed, or no deleted accounts are found in the user file,
    the next valid account is assigned as the reserved account.

<span id="anchor-691"></span>A password, access level, and number of credits will be prompted for.
==================================================================================================

After this information is entered, the BBS reserves that account.

### <span id="anchor-692"></span><span id="anchor-693"></span><span id="anchor-692"></span><span id="anchor-694"></span><span id="anchor-692"></span><span id="anchor-693"></span><span id="anchor-692"></span>+.weed

The weed program allows you to automatically go through your user files,
and delete users who have not called within a specified amount of time.

<span id="anchor-695"></span>To use it, run +.weed.  You are asked if you would like auto-weed, or selective weed.
==================================================================================================================

-   "Selective weed" prompts whether you want to delete each user that
    it finds before deleting them.

<span id="anchor-696"></span>It also includes users with non-weed status, since you will be prompted.
=====================================================================================================

-   Auto-weed doesn't prompt, but deletes each user it finds that has
    not called since the cut-off date.  (Non-weed status users are
    ignored in this mode.)  You are asked for the cut-off date, which
    will be the date that is checked against the last call date.

Enter it in the format shown, then tell the program which ID number to
start from.  Everything else works automatically, and you hear a beep
when the program is finished.

<span id="anchor-228"></span><span id="anchor-697"></span><span id="anchor-228"></span>AutoWeed system
------------------------------------------------------------------------------------------------------

### <span id="anchor-698"></span><span id="anchor-699"></span><span id="anchor-698"></span>+.access

This is used to edit your access groups. You must reboot in order for
the access information to take effect.

### <span id="anchor-700"></span><span id="anchor-701"></span><span id="anchor-700"></span>+.reconfig

This program allows you to re-define such things as number of calls to
the system, board name, prime time, etc.  Simply run it and follow the
prompts to use.

<span id="anchor-702"></span>+.reledit
======================================

*This documentation was modified slightly from the text files on the
RELedit and Networking plus-file disks.  I in no way take credit for the
original documentation, just the cleanup and integration into these more
current, streamlined docs.*

RELedit is a program which eases the setup and administration of message
and file transfer bases.  Just run *+.reledit* from the main prompt.

After a short delay as RELedit reads the system configuration, you see
the main menu.  Across the top is the title of the program and a
copyright message.  Below that is data on your BBS that includes the
number of Subs, U/Ds, etc. that are defined, as well as your node number
if you are on the network.  Below that are 5 options:

***S – Sub***

***U - U/D***

***X - U/X***

***G – SIG***

***N - NetSubs***

Select S, U, X, G or N.

*Note*: If you are not part of a network, the NetSubs option will not
appear.  This documentation assumes you are networked.  If not,
operation is exactly the same, you just can't use the NetSub option.

<span id="anchor-703"></span><span id="Editing Sub-Boards"></span><span id="anchor-703"></span>Editing Sub-Boards
-----------------------------------------------------------------------------------------------------------------

If you select S, the BBS enters the Sub-board list editor's first
screen.  It consists of a listing of the Subs (if any) you have defined.

The list of Subs show:

-   The title
-   Type
-   Whether it is open or closed
-   The device and drive the messages are saved to
-   The ID number of the SubOp (ID\# 0 means no SubOp)
-   The password (if any)
-   The access level required to see/enter it
-   If it is a NetSub, a small n will appear after the access level.

To add a Sub, type A and hit RETURN.

### <span id="anchor-704"></span>Ranges

Typing ranges of sub-boards to add, delete, move, or insert works
similar to BASIC's LIST command.

  --------- -------------------------------------------------------------------------------------------
  --------- -------------------------------------------------------------------------------------------

Type the board number you want to edit, then press *RETURN*. (Pressing
*RETURN* by itself exits to the main RELedit menu.)

<span id="anchor-705"></span>Editing Sub-Board Options
------------------------------------------------------

A menu appears with 9 options:

  ---------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ---------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Table : RELedit sub-board definitions

These 9 options are the same for the U/D and U/X editors as well.  The
only difference is the ***Type*** question which asks ***Downloads
Only?*** and ***Free Downloads?*** as well as Password.

If the access is 0 or the title is ---, the data will not be saved (or
deleted if editing an existing record).  The BBS also goes through the
SIGs (if defined) and removes the board from any SIGs it is on.

<span id="anchor-706"></span><span id="anchor-707"></span><span id="anchor-706"></span>The SIG Editor
-----------------------------------------------------------------------------------------------------

This is much like the Sub, U/D and U/X editors.  The list displays:

-   the SIG title
-   access
-   the SIGop ID
-   whether the Subs, U/Ds and U/Xs are open in that SIG

Another new feature found in this version of RELedit (when coupled with
the newest version of the TurboRELs) is the ability to "close" a section
of the board to a SIG.  What this does is prevent the SIG from being
listed when the user enters the "closed" section.

For example, if you have a SIG that shows the U/X section closed, when a
user types "UX", the SIG will not display, appearing as if the SIG does
not exist in that area.

When you type the number of the SIG you wish to edit, the following
options appear:

  -- -------------------------------------------------------------------------------------------------------------------------------
  -- -------------------------------------------------------------------------------------------------------------------------------

Table : RELedit SIG editing options

### <span id="anchor-708"></span><span id="anchor-709"></span><span id="anchor-708"></span>Editing Lists

Using options 7 through 9, you are presented with a list of the Subs,
U/Ds or U/Xs (depending on what option you select) that looks very much
like the one users see when listing the available boards in SB/UD/UX.

Everything is keyed off of the position of the board in that list.  For
example, if you enter *D5* it will delete the 5th board in the list of
boards for that SIG.

The commands are as follows:

*\[A\]dd board*

**

Add a board to the end of the list of boards for this SIG.  This command
accepts ranges, or type just A and you are asked for the board number
(which is the record number you saw in the Sub, U/D and U/X editors).

Typing *L* at the main ***Edit*** prompt or the ***Add Which*** prompt
lists the defined Subs/UDs/UXs (depending on which type you are
editing).

The Add command also allows multiple adds by giving it a range to add.
For example, A5-10 will add Subs 5 to 10. Range commands also work at
the "Add Which" prompt.

*\[I\]nsert board*

**

Identify the number *before* the board(s) you want inserted. Typing *S*
at the edit prompt or the ***Insert Before Which*** prompt lists the
boards in that SIG (again, you can enter a range here as well).  You can
give the board number you want the new boards inserted before by typing
*I* followed by the number.

  ------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Pressing *RETURN* saves the list, returning you to the editing screen
for the SIG information.

When you hit RETURN at the SIG Edit prompt, the data is saved unless the
title is *---* or the access is 0.

If a SIG is deleted, the SIG list for that SIG is also deleted.

<span id="anchor-710"></span><span id="anchor-711"></span><span id="anchor-710"></span>Netsub Editor
----------------------------------------------------------------------------------------------------

This editor lets you list all of the NetSub IDs you have (you can have
up to 60) and edit the lists of boards they are linked to as well as
what sub-boards on your BBS are part of that NetSub.

To define a networked sub, first set it up ([Editing
Sub-Boards](#Editing Sub-Boards), page [67](#Editing Sub-Boards)).

When you hit N at the main prompt, the BBS looks on your disk for the
NetSub data files.  These files are program files that are loaded into
memory using one of the new protocol files written for the NetSubs.

NOTE: If you have a Lt. Kernal, have the Autoload feature turned on, and
have a floppy drive with the same device number as the Lt. Kernal, you
get a flashing error light on the floppy drive when you enter the NetSub
editor as well as every time the new *+.NM.netsub* files are executed
during Network Maint.  You might want to remove the floppy drive from
your system if this bugs you, but it will not hurt the operation of
RELedit or the BBS.

The list only displays the NetSub IDs you have defined on your BBS.

Type the number on the left of the NetSub ID you wish to edit and you
are taken to the editing screen.

You will now see 18 options:

Option \#1 lets you modify the NetSub ID.

Options \#2 through \#17 are Network IDs of the boards that this NetSub
is linked to.  This list should only contain the IDs of boards that you
send NetSubs directly to, not every board that is linked to that NetSub
anywhere on the network.

The board IDs are *not* verified.  This is inline with the new network
design and the reasons for this will be explained when the Image Network
is reorganized to make use of the new network features.

Option \#18 lets you define which boards on your BBS are parts of this
particular NetSub.

The editor that is entered when you select option \#18 is very much like
the SIG list editor.  (As a matter of fact, both the SIG editor and
NetSub editor use the same routines!)  The only differences are as
follows:

-   Up to 60 boards can be defined as being part of a particular NetSub.
-   You can only add boards that are not already identified as
    being Networked. \[To remove Network status from a particular
    sub-board, it must be deleted and re-added using the Subs editor.\]
-   The "Multi-Add" and "Multi-Insert" functions skip not only deleted
    records, but already networked boards.

While the order of the subs in this list does not in any way affect the
order in which they are listed to users, it does affect the order in
which they are scanned when *+.NM.netsub* is run. When a message comes
in to a board, the boards are searched for a post of the same name in
the order defined in this section.  If none are found, the boards are
scanned in the same order again for a place to post a new message.

You may want to rearrange the order of the Subs to speed up NetSub
operation.  For example: if you have a sub containing older posts not
responded to as often as a sub found later in the list, you might want
to switch their order so the board with more activity comes first. This
way the BBS does not read through older posts for no reason.

### <span id="anchor-712"></span><span id="anchor-713"></span><span id="anchor-712"></span>Overflow Subs

This is a system allowing you to set multiple boards as being part of a
particular NetSub ID.  When a network message comes in, all subs part of
a particular NetSub ID are searched, and the response (or new post) is
added where appropriate.

That should just about cover the options available to you in the new
RELedit.  I hope you enjoy it and find it useful in maintaining your
BBS.

<span id="anchor-714"></span><span id="anchor-715"></span><span id="anchor-714"></span><span id="anchor-716"></span><span id="anchor-714"></span><span id="anchor-715"></span><span id="anchor-714"></span><span id="anchor-317"></span><span id="anchor-714"></span><span id="anchor-715"></span><span id="anchor-714"></span><span id="anchor-716"></span><span id="anchor-714"></span><span id="anchor-715"></span><span id="anchor-714"></span>Nightly AutoMaint
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The "AutoMaint" feature in +.lo is designed as a building block to add
nightly maintenance functions—you may add any sort of functions you
wish.

As it now stands, it will rotate the caller and AutoMaintenance logs
every night at midnight (or as soon as possible thereafter, if a user
happens to be online at around that time, AutoMaintenance is delayed
until after they log off).

A week's worth of logs are maintained under the filenames e.log x (where
x is the day of the week: 1=Sun...7=Sat, like setting the weekday when
changing the BBS clock manually).  They may be viewed with the LG
command online.

Anyone with limited disk space who does not wish to use this feature can
set the variable am to 0 in line 1 of +.lo, and use +.NL (New Log)
whenever the log reaches a certain size.

<span id="anchor-717"></span>Networking
=======================================

<span id="anchor-718"></span>About NetMail
------------------------------------------

IMAGE NETMAIL V1.2.4 DOCUMENTATION

Copyright 1990, New Image Software

UPDATED 7-1-90

NetMail 1.0 is a system which allows files to be transferred between
BBSes automatically. In this version of NetMail, it supports E-Mail
transfers among users, and general file transfers among sysops. Also, if
the TurboREL SIGs are used, Network Sub-Boards are available.

All of this is accomplished by means of a program called *+.NMauto*.
This program is run automatically by the system at regular intervals.
(Usually one hour apart.) The program checks for the existence of files
that need to be transferred to other systems. If any exist, the
necessary phone calls are made, and the files are transferred.

Each node in the network will need to pick a node ID. This is just a 3
character identifier that will represent that node. We suggest that an
abbreviation of the BBS name be used so that it will be familiar.

### <span id="anchor-719"></span>NetMail Paths

To avoid the problems of having your BBS call *all* of the other nodes
on your network, the number of connections that can be made to any node
is four. At first, this may seem like a small number. However, in our
testing, we have found that it keeps the traffic through any one node
low enough, and limits the number of calls that any one node has to
make.

Node IDs are used in paths. For example, say you had a network with 6
nodes in it. The path from, say LDE to GFD might be ***/LDE/WZK/GFD/***,
whereas the path from JMS to PGN might be ***/JMS/LDE/PGN/***. The path
describes how to send files from one place to the other. For the most
part, you will not need to worry about paths. You just need to know that
they are there.

One other restriction is placed on the layout of the network. That is
that there can only be one path between any two nodes in the network. If
the network is planned with *any* loops in it (places where files could
be sent in circles) then the network will have problems.

### <span id="anchor-720"></span>Network Maintenance

One BBS on the network will be responsible for network maintenance. It
is the sysop of this BBS who will set up the paths that were described
above. It is not up to this sysop to plan all of the paths, just to
configure them into the network.

The sysop in charge of the network also has the ability to send
"NetNews.” This is a news file that will be automatically installed on
all of the nodes in the network. The purpose of this is to provide a way
to relay current information about the network to all of its users. Such
information might include new nodes that have been added or local news
that is of interest to everyone.

### <span id="anchor-721"></span>Network Planning

Planning a network is not as difficult as it may seem. There is a simple
method of planning a network of any size. You get a piece of paper, and
write the node ID of your BBS in the middle of it. Then draw four long
lines, one going up, down, right, and left. These are places where you
can add nodes. Write the IDs of the nodes at the ends of the lines. Then
draw three short lines from each of these. (See [Figure 1: Simple
network](#anchor-722).) Add nodes on the end of each line. The process
can be continued indefinitely.

Note that you could not connect PCM to JMS because that would cause a
loop, as mentioned above.

**

* |*

* -PCM-*

* |*

* |*

* | | |*

*-WZK---LDE---JMS-*

* | | |*

* |*

* |*

* -PGN-*

* |*

**

<span id="anchor-722"></span>Figure 1: Simple network

<span id="anchor-723"></span>General Setup
------------------------------------------

### <span id="anchor-724"></span>Where to Put the Files

These files should be put on your Plus Files disk:

  ----------------------------------------------- ---------------- ---- -----------
  ----------------------------------------------- ---------------- ---- -----------

Table : Networking Plus Files

###

### <span id="anchor-725"></span>Installing NetMail

You will need to make two small changes to Image in order to make
NetMail run on your system. Line 1 of the program *+.lo* has *nf=.* or
*nf=0* in it. It needs to be changed to read *nf=1*. The same is true of
the program *+.EM*.

If you have a very busy BBS, you may also want to change the *rs=.* (or
*rs=0*) in line 1 of *+.lo*, to read *rs=1*. This will reserve your
system from 3-4 AM each night, so that NetMail will get through.

### <span id="anchor-726"></span>Getting Ready to Go!

This is the most important part. You need to find someone to network
with. Once you find someone, or a group, you need to decide who is going
to be the network operator. At this point you would skip forward to the
appropriate section. If you are the network operator, read the section
entitled **Creating A New Network**, and if you are not, then read the
section entitled **Joining An Existing Network**. If you want to join
the existing Image Network that we are running, contact THE CHIEF on
Port Commodore (THE CHIEF @ PCM, in Net-Lingo).

<span id="anchor-727"></span>Creating a New Network
---------------------------------------------------

### <span id="anchor-728"></span>Network Planning

Plan your network. Get out paper and a pencil, and draw a map. Try to
avoid long distance calls by "chaining" nodes together. You will need to
get all of the available information about the BBSes that will be in
your network. It's not hard to add new nodes later, but it is hard to
remove them once they are there. One of the easiest ways to plan the
network is to first find 4 nodes to connect to your node. Then work on
finding 4 to connect to each of those. However, it is not necessary to
fill up all of the connections. You can leave some open so that you can
later expand. See [Figure 2: NetMap 6-20-90](#anchor-729) which has the
current map of the network that we are running.

Note that we have left plenty of room left to expand, and welcome anyone
to join.

Assign each of your nodes a number. Start with 1, which will be your
node, and then number the rest. This will be important later.

*ABC-REG WZK SCJ RRT-TNS \
| | | | *

*STF-JMS GFD-CHF-DAG-GOC FII-SBD *

* | | | *

*SSF-PGN-LDE---------PCM-TCN-SOK-ECY*

* | | *

*EFB-GJ2-PAD RHQ-FRW-LDW *

* | | | *

*TRN | SWD TFD TYP CRO-LOZ *

* | | | | *

*LKR-CMR-LWR-WN2-TWB *

*| | | | *

*TTC | TGD | TBB TER SPT D38 *

*| | | | | | *

*CST-DRC-INI | INS DII-MMA-ALD *

*| | | | | | | *

*CSP MIA TCB-WN3-TWZ-ASN CDX SOM *

*| | *

*TPO-TAH-TTS-SSW-TGI HCL *

*| | | *

*CIA-TST WOL TOS *

**

<span id="anchor-729"></span>Figure 2: NetMap 6-20-90

### <span id="anchor-730"></span>Configuring Your Network

Now comes the fun part. From within Image, run the + file *+.NM/utils*.
Since you have never configured a network on your system, it will ask
you if you want to create a network. Say Yes.

Then, you will be taken to the Utilities menu. There are several options
available. You will need to edit the nodes, using option A.

You need to edit node 1, and put your info into it. Make sure to set
*everything*. Then, add the other nodes in the same way.

Note that you need to change the connections while in the node editor.
When changing a connection, you need to make sure that you edit *both*
nodes to make the connection complete. Leave any empty connections as
*0*. When you are done, press *RETURN* to get back to the utilities
menu, and select the option to ***Make 'nm.create'***. This will make
the file that you must give to each of the sysops in your network so
they can configure themselves in. You must also tell each sysop what
his/her node \# will be.

You will also have to tell the sysop of each node who will be connected
to them. They will all need to make up passwords for their nodes, and
each one will need to give their passwords to the sysops of the nodes
that are connected to them.

When you are done, run the program *+.NM/config*. You need to set *all*
of the different options, so just go through each of the menu items.

Everything in the section **Joining an Existing Network** will apply to
you as well, so you should read that section also.

### <span id="anchor-731"></span>Adding a New Node

When you need to add new nodes, just enter the Node List Editor again,
and add them in. Make sure to edit the nodes they are connected to so
that they will be connected in both directions. When you are finished,
make the *nm.create* file again, and be sure to give this to the new
network members. They will configure just as the original members did.
Don't forget to give them their node numbers.

Next, you *must* send a Node Update. This will send a file out to the
other BBSes in your network to tell them what changes have been made. It
will automatically install the changes in their system.

<span id="anchor-732"></span>Joining an Existing Network
--------------------------------------------------------

### <span id="anchor-733"></span>Configuring Your System

You will need to get a copy of the file *nm.create* from your network
operator. Put this file on your Email disk. Also, you need to find out
what your node number is, and what BBSes are connected to you. You will
need to make up a password, and give it to each of the sysops of the
BBSes who are connected to you. They will have to give you their
passwords as well. Be sure to go through each of the options in the
configuration menu to make sure that they are set correctly.

If you wish to have the modem be off hook while NetMail is doing its
work, turn the "Off Hook" flag on. Note that this will not work with
*all* modems. Also note that NetMail will not work with modems that do
not accept Hayes-type commands.

An explanation is needed for the connection editor. What you must first
do is decided when you want calls to be made by the BBS, based on what
"type" of day it is. For example, perhaps on weekends you want to allow
24 hour calling, while on weekdays you only want calling at night. The
24 hour type is pre-defined as "+". So you must configure another type
to have the hours you want for the weekends.

The option "Change call times" is what you use to edit the types. You
would set the first call type 0 to the hours you want to allow. If you
want to define other types, you have the 1 to 9 to work with as well.

After defining the types, you should use the option to "Edit
connections". That will bring you to another menu. Choose "Normal
Connections". (The other option, "Shortcuts" is not yet fully
implemented, but will be in future versions.)

When editing the nodes, you can enter the passwords, define the type of
day for each day of the week (for calling hours) and set the number of
calls per day for each day of the week.) When setting the calls/day, "+"
means infinite calls. When setting the types of days, "+" means 24 hours
and "-" means no calls that day.

Once you finish configuring, you are all set! NetMail is up and running
on your system. Any time more nodes are added, it will automatically add
them into your system.

<span id="anchor-734"></span>E-Mail Forwarding
----------------------------------------------

E-mail forwarding lets you pick a few people whose E-mail will be
automatically sent from your BBS, though the network, and end up on some
other BBS. For example, it might be nice to forward E-mail for the
sysops of the other BBSes on the network. There is an option on the
configuration menu for this. You need to specify what their handle is on
your BBS, and what it is on the destination BBS, and, of course, what
the destination BBS is.

<span id="anchor-735"></span>NetMail Online Functions
-----------------------------------------------------

NetMail adds several commands into the e-mail section of Image BBS.
Those commands are listed here, along with descriptions of what they do:

  ------ ------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------
  ------ ------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------

Table : NetMail Commands

<span id="anchor-736"></span>Network File Transfers
---------------------------------------------------

Files may be transferred between sysops through the network. There is a
separate program to do his, it is called *+.NM/file*. When files are
transferred, they are put into a special *nm.F* file. This allows
multiple files to be sent at one time, by just sending a single file.
When you receive files, it will notify you in your e-mail. You should
then run this program.

When you run the program, it will scan to see if any of these *nm.F*
files are waiting for you. If any are, it will ask you if you want to
extract the files. Extracting the files will put them on the Email disk,
so be sure you have enough room. The program will tell you the length of
the *nm.F* file. The extracted files will have approximately the same
number of blocks total.

When that is finished, or if there were no files received, it will ask
you if you want to send files. The prompts are self-explanatory here.

Keep in mind that some of the Nodes that you send files though may not
have enough disk space to hold the file (even temporarily) while it is
waiting to be sent on to the next node. It is not generally a good idea
to send a *lot* of files at a time for this reason, or very large files.
Also, since some of the connections may be long distance, you may be
running up someone's phone bill considerably. (And yes, they will know
exactly who did it because they will know where the files came from, and
where they were going. You don't want to get your fellow network members
mad at you!)

<span id="anchor-737"></span>NetGrf/NetWall
-------------------------------------------

Two versions of the Network "Wallwriter" are supplied with the Network.
One is the *normal* Wallwriter with network abilities added. The other
is a 10-line version that allows a lot more text. MCI commands are *not*
allowed on the wall, but color codes and graphics are. Both versions can
be accessed by the program *+.NW*.

The easiest way to install NetWall is by adding it into your *PF*
section. Or, you could add it in as a command in your *im* file. (This
is only suggested if you are familiar with doing such things.) The other
option, and some people have already done so, is to merge it into your
*+.on* file, so that it can be used during the logon sequence, just as
Wallwriter is.

There is one important thing to know about the NetWall. It will get
*big! Very big!* As responses come in from all over the network, they
will accumulate. It is up to you to keep it to a useable amount. When
you run *+.NW* while in Local Mode, it will ask you if you want to edit
the wall. This will allow you to selectively delete messages from the
wall. Deleting them on your system *will not* delete them from other
systems, so you are free to keep as many as you like, or as few as you
like. We suggest that you check the size of the file at least once a
week.

There is also a Weed option that will do this for you. You only need to
tell it how many days back to set the cutoff point, then it will delete
the messages older than that day.

If you do *not* want to use the NetWall, then you should change the
*g1=1* in line 801 of *+.NW.walls* to *g1=0*. This will turn the 10-line
version off.

If you do *not* want to use the Network WallWriter, then you should
change the *g2=1* in line 801 of *+.NW.walls* to *g1=0*. This will turn
the 1-line version off.

<span id="anchor-738"></span>NetMail Support/Information
--------------------------------------------------------

If you wish to have any further information about netmail, you can
contact PROFESSOR, on Lyon's Den East. The phone number is (313)
453-2576.

<span id="anchor-739"></span>Compatibility Notes
------------------------------------------------

This software has been tested on the following list of equipment:

COMPUTERS

Commodore 64

Commodore 128 in 64 mode

MODEMS

Commodore 1670 (old and new)

Supra 2400

Transcom 1200H

Aprotek 2400 (minimodem)

DISK DRIVES

Commodore 1541, 1571, and 1581

Commodore SFD 1001 W/IEEE Flash

Lt. Kernal Hard Drives

Please note that we cannot guarantee that it will work with anything
that is not on this list. However, most modems are compatible with those
tested, as are most disk drives. As a general rule, most equipment that
will work with IMAGE BBS, will work with NetMail.

<span id="anchor-740"></span>The IMAGE Network
----------------------------------------------

As we have mentioned in several places in this manual, we are running
this network software on our Image Support BBSes. This network is
growing fast, and any who have bought the NetMail software are welcome
to join it. There is only one catch. In order to join our network, you
have to find someone who is already on our network who is willing to
sponsor you. If you are local to one of our nodes, then this is usually
not a problem. But if you are not local, then you must find someone who
is willing to connect you *long distance* to their BBS.

This is not usually a problem. A typical long distance network call
lasts about 3-4 minutes, and they do not necessarily occur every night.
Using 2400 baud helps a lot for the phone bill, as it will take only
half the time to send the same files. Estimates are at about \$30 a
month for a long distance connection.

In the future, we may request that sysops who do not have long distance
connections on their nodes to voluntarily contribute \$15 - \$25 per
month, which would be given to those sysops that do have long distance
connections. The idea being to share the costs a bit, so no one has to
bear the whole burden.

<span id="anchor-741"></span>Programming Notes
----------------------------------------------

### <span id="anchor-742"></span>E-Mail System

The e-mail system for Image 1.2 was written while the Network was in the
planning stages, over a year ago. Several "hooks" were put into it so
that when the Network was available, E-Mail would be ready. The file
*+.NMextra* is a mini-module that E-Mail loads when NetMail is active.
The routines in *+.NMextra* handle all of the network functions that the
users can access.

### <span id="anchor-743"></span>Configuration Editors

The file *+.NM/config* is a stand-alone module that handles all of the
network configuration that a sysop would need to be able to do.

The file *+.NM/utils* is a stand-alone module that handles the Network
Administrator's functions.

### <span id="anchor-744"></span>Network Maintenance

The file *+.NMauto* is loaded by the *+.lo* program whenever Network
Maintenance needs to be done. It is this module that handles incoming
and outgoing calls. In addition to *+.NMauto* there are several
mini-modules that process files as they are received. These include
processors for Mail, the Netwall, NetNews, Updates, and so on. Also,
when the TurboREL Sigs are used, there are processors for NetSubs.

### <span id="anchor-745"></span>ML Support

There are a few ++ files that do a lot of the "dirty work" for the
network.

  ----------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ----------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Table : NetMail Plus Files

### <span id="anchor-746"></span>Future Changes

More additions are planned for the network system. A few online games
that send results via the net are planned, and some new features are
going to be added to e-mail. Updates will be available on Lyon's Den
East, and other Image Support BBSes.

<span id="anchor-747"></span><span id="anchor-748"></span><span id="anchor-747"></span><span id="anchor-749"></span><span id="anchor-747"></span><span id="anchor-748"></span><span id="anchor-747"></span>Programming and Troubleshooting
==========================================================================================================================================================================================================================================

This chapter provides programming information for those interested in
the programming details of IMAGE BBS, and troubleshooting information
for those that may be having problems.

<span id="anchor-750"></span><span id="anchor-751"></span><span id="anchor-750"></span>Overall Description
----------------------------------------------------------------------------------------------------------

IMAGE BBS is a modular program, consisting of both BASIC and machine
language files interchanged by the program to add the capability of
never running out of memory for program space!  It performs this miracle
by loading modules (overlays) when needed to perform specific tasks.
Using this technique, you may do about anything you wish to on the BBS,
not worrying about memory constraints.

Of course, every great concept has its drawbacks, and this one is no
exception.  The price we have to pay for it is the fact that loading
these modules takes time, slowing down the BBS somewhat, since you must
wait for them to load.  However, we feel the trade-off is well worth
it!  If you have a RAM Expansion Unit, CMD RAMLink, or faster disk drive
(IEEE, Lt. Kernal, CMD HD, etc.), the load process is speeded up
considerably *or is in some cases instantaneous*, and helps quite a
bit!  Those that do not experience more waiting, but no loss of
capabilities on the BBS.

The BBS was written with the programmer in mind.  Special attention was
given to making it easy to modify and customize.  Several custom
features can be added without even changing the program, but if you can
program in BASIC a little, you'll be surprised at how easy it is to add
your own ideas.

<span id="anchor-752"></span><span id="anchor-753"></span><span id="anchor-752"></span>Modules
----------------------------------------------------------------------------------------------

IMAGE uses a main BASIC program (*im*), and several machine language
modules (the *ml.\** files) which remain in memory at all times.  It
also uses BASIC modules (*+.\** files), and machine language modules
(*++\** files).  You may write as many of your own modules as you'd
like, adding them at any time.  The main consideration is to know which
variables and subroutines to use, and how to use them.  Be careful when
modifying the main program (*im*) so you do not add too much, or you
will find yourself running short on memory, slowing down or possibly
crashing due to being short on free memory.

Adding to a plus-file cannot hurt, as long as you do not go over 56 CBM
disk blocks for any individual module.  However, defining new
variables—especially arrays—can eat up memory and cause the
same problems mentioned above, so be selective in your variable usage.
There are many routines in the program which are available for you to
use.  We will describe a few of the most commonly used here.  This is
*not* meant to be a detailed guide to programming, only a brief
description so you may get the idea.

*I have HTMLized the programmer's reference guide, and am working on
continuing to improve it.*

<span id="anchor-754"></span><span id="anchor-755"></span><span id="anchor-754"></span><span id="anchor-756"></span><span id="anchor-754"></span><span id="anchor-755"></span><span id="anchor-754"></span><span id="anchor-757"></span><span id="anchor-754"></span><span id="anchor-755"></span><span id="anchor-754"></span><span id="anchor-756"></span><span id="anchor-754"></span><span id="anchor-755"></span><span id="anchor-754"></span>Common Subroutines
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+
|  |
+--+

<span id="anchor-758"></span>Table : Common subroutines

<span id="anchor-759"></span>Variable Handling in Modules (Plus-Files)
----------------------------------------------------------------------

IMAGE variable usage in programming modifications and modules should be
done carefully.  If you were to change any variables that the BBS uses
for particular functions, you could be in serious trouble!  This could
corrupt your user files, or do any number of nasty things!  Because of
this, we are giving you a list here of all system variables that you
should *never* use.  Even if you are using "temporary" variables, make
sure any subroutines in the main program or program module you are
modifying do not change these variables and wreak havoc!  Most
one-letter variables, integer variables, and string variables are
usually OK to use (with a few exceptions noted below).

Variables not in this list are cleared when the main prompt is reached,
so don't use one to count the number of times a game is played per call
in that manner; the BBS will not permanently remember it.  However, the
same routine allows you to DIMension variables and arrays in modules
without worrying about a "?redim'd array error".  Be careful not to
waste memory with excess variables, or your modules will run slowly, and
possibly even crash the BBS.

Here is a list of reserved system variables that you should NEVER use,
except for their intended system functions:

Since I think it's sort of important to know what the variables are
actually *used* for, and not just their names, I'm going to steal a page
from the *Image BBS Programmer's Reference Guide* and explain their
meanings to the best of my ability.  Feel free to set the record
straight if you know otherwise, 'k?

### <span id="anchor-760"></span><span id="anchor-761"></span><span id="anchor-760"></span>Reserved String Variables

  -------- -------------------------------------------------------------------------------
  -------- -------------------------------------------------------------------------------

<span id="anchor-762"></span>Table : Reserved string variables

### <span id="anchor-763"></span><span id="anchor-764"></span><span id="anchor-763"></span>Reserved Integer Variables

The current reserved integer variables for Image v1.2 are as follows:

  ------- ------------------------------------------------------------------------------------
  ------- ------------------------------------------------------------------------------------

<span id="anchor-765"></span>Table : Reserved integer variables

### <span id="anchor-766"></span><span id="anchor-767"></span><span id="anchor-766"></span>Reserved Floating Point Variables

The current reserved floating point variables for Image v1.2 are as
follows:

  ------- ------------------------------------------------------------
  ------- ------------------------------------------------------------

<span id="anchor-768"></span><span id="anchor-769"></span><span
id="anchor-768"></span>Table : Reserved floating point variables

<span id="anchor-770"></span><span id="anchor-771"></span><span id="anchor-770"></span>Arrays
---------------------------------------------------------------------------------------------

The following arrays are dimensioned by the BBS.  Most can be used for
your own programs, except where noted.

  ------------- -------------------------------------------------------------
  ------------- -------------------------------------------------------------

Table : Reserved Arrays

<span id="anchor-772"></span>

(from programmer’s ref guide)

   AC% User's current access level

   AC%(

   AG\$ Access group name

   AK\$ "Line divider;" space, LL%-2 "-"'s, RETURN character

   AN\$ Last user input

   AO% User's old access level (used in access level change situations)

<span id="anchor-773"></span>   BD
==================================

<span id="anchor-774"></span>   BF( Number of blocks free on the six system disks
=================================================================================

   BN\$ BBS name

   BU

   CL\$ I think this is C1\$ instead; "Entering chat" message

   C2\$ "Exiting chat" message

   C3\$ "Returning to editor" message (fixme: pretty sure anyway)

<span id="anchor-775"></span>   CA
==================================

<span id="anchor-776"></span>   CC\$ 2-character BBS identifier
===============================================================

   CM\$ Displayed in the "Area" section \[when the top screen mask is
enabled\]

<span id="anchor-777"></span>   CN
==================================

<span id="anchor-778"></span>   CO\$( User's computer type name array
=====================================================================

   CO% User's computer type number array

   CR

   CT

   CT% BBS calls today?

D1\$ 11-digit current date/time

   DL\$ Again, D1\$? bad ocr?

   DL% Again, D1%? bad ocr?

<span id="anchor-779"></span>   D2\$
====================================

<span id="anchor-780"></span>   D2%
===================================

   D3\$ Last user on BBS

   D4\$ Current ML protocol

   D5\$ True last call (date? fixme: more info)

<span id="anchor-781"></span>   D6\$
====================================

<span id="anchor-782"></span>   DA%
===================================

   DC

   DC%

   DD\$

   DR Set 1-6 to designate system drive \#

   DR\$

   DV%

   DV%(

   EL

   EM User's expert mode: 0=off, 1=on

   F1

   F2

   F3

   FF\$ User's real first name

   FL

   FL\$

   F1\$(

   GS

   I1\$

   I2\$

   I3\$

   ID User's ID number

   KK Lines of text in BBS editor; if 0, aborted or time limit expired

   L1

   LC

LD\$ User's last call date (11 digits, like D1\$)

<span id="anchor-783"></span>   LE
==================================

<span id="anchor-784"></span>   LF User's linefeed flag?
========================================================

   LL\$ User's last name

   LL% User's line length

   LP

   LT\$

   MF 11-digit date format of user's last call

   MW

   NA\$ User's handle

   NC

   ND

   NL User's current graphics mode: 0=ASCII, 1=Commodore C/G

   NL\$ CHR\$(0), a null character

   NP

   NR

   NV

   OC\$

   P\$

   PL% P1%?

<span id="anchor-785"></span>   P2%
===================================

<span id="anchor-786"></span>   P3%
===================================

   PH\$ User's phone number

   PL

<span id="anchor-787"></span>   PM
==================================

   PO\$ Main prompt string

   PP\$

   PQ

   PR

   PR\$

   PS \# of posts?

   PT% Probably a prime time flag

   PU\$

   PW\$ some password

   QB bits per second rate ("current baud")

<span id="anchor-788"></span>   QE
==================================

<span id="anchor-789"></span>   QT\$ CHR\$(34), a quote character
=================================================================

   R\$ CHR\$(13), a RETURN character

   RC

   RN\$  User's real name (FF\$ + " " + LL\$)

   RP   \# of responses

   RQ

   RS

   SH   Updated by ML routines; "spacebar hit": 0=no, 1=yes

   SO%( Subop array, used in SB, UD, UX subsystems

   SR Logical file number in certain routines

   ST   Commodore BASIC reserved variable; serial status

   ST(

   SY\$

   T1

   TC%  Total calls to system (grand total?)

<span id="anchor-790"></span>   TF
===================================

   TI   Commodore BASIC reserved variable; jiffy clock

   TI\$  Commodore BASIC reserved variable; 24-hour clock

   TR%  User's time remaining, in minutes

   TT\$( Lines of text stored in editor

   U\$ Stacked commands

   UC

   UH   Highest user account \# in user file?

<span id="anchor-791"></span>   UL
===================================

<span id="anchor-792"></span>   UR
===================================

   X\$

<span id="anchor-793"></span><span id="anchor-794"></span><span id="anchor-793"></span>Image Output Routine
-----------------------------------------------------------------------------------------------------------

In order to send text to the modem and screen (PRINT, for you BASIC
people) as easily as possible, we have developed a routine that works
very similar to the BASIC PRINT statement.  Used properly, this routine
also eliminates much of the garbage collection that the C64 is notorious
for.  Just as many are used to using the question mark as a shortcut to
PRINT something in BASIC:

*?"Hello There!"*

You may use the ampersand (*&*), IMAGE's "print" character, to do the
job:

*&"Hello There!"*

will have the desired effect in the BBS environment!  Well, almost.  By
default, Image displays the above like using PRINT with a semicolon on
the end.  (That does not move down to the next line when finished
PRINTing the current line.)  If you want a carriage return to separate
lines, add one anywhere inside quotations by typing function key *F6*,
which displays *K*.

*&"Hello There!K"*

You may also:

*&an\$* or *&tt\$(x)*(anything using a string variable)

- BUT -

*&str\$(i)*(numeric variable output is not supported yet.)

Some oddities in syntax:

-   You must follow a *THEN* clause with a colon before using the
    ampersand.  In other words:

*if b then &"hello"(*will not work)

*if b then:&"hello"(*must be used instead)

-   If the ampersand is used all by itself:

*b=b+l:&:if b then ...* (*&* outputs the contents of *a\$*)

<span id="anchor-795"></span><span id="anchor-796"></span><span id="anchor-795"></span><span id="anchor-314"></span><span id="anchor-795"></span><span id="anchor-796"></span><span id="anchor-795"></span>Other & Calls
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The ampersand is also used with arguments to call all of the machine
language routines in IMAGE BBS.  The table of arguments that are useful
in BASIC and a brief description follow:

  ------------ ----------------------------------------------- ----------------------------------------------------
  ------------ ----------------------------------------------- ----------------------------------------------------

Table : & calls

<span id="anchor-797"></span><span id="anchor-798"></span><span id="anchor-797"></span><span id="anchor-799"></span><span id="anchor-797"></span><span id="anchor-798"></span><span id="anchor-797"></span><span id="anchor-800"></span><span id="anchor-797"></span><span id="anchor-798"></span><span id="anchor-797"></span><span id="anchor-799"></span><span id="anchor-797"></span><span id="anchor-798"></span><span id="anchor-797"></span>POKEs
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

This is a list of some of the memory locations used by IMAGE that can be
usefully POKEd:

  ------------------- ---------------------------------------------------------------
  ------------------- ---------------------------------------------------------------

Table : Useful POKE locations

<span id="anchor-801"></span><span id="anchor-802"></span><span id="anchor-801"></span><span id="anchor-803"></span><span id="anchor-801"></span><span id="anchor-802"></span><span id="anchor-801"></span><span id="anchor-804"></span><span id="anchor-801"></span><span id="anchor-802"></span><span id="anchor-801"></span><span id="anchor-803"></span><span id="anchor-801"></span><span id="anchor-802"></span><span id="anchor-801"></span>Common Modifications
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### <span id="anchor-805"></span><span id="anchor-806"></span><span id="anchor-805"></span><span id="anchor-807"></span><span id="anchor-805"></span><span id="anchor-806"></span><span id="anchor-805"></span><span id="anchor-808"></span><span id="anchor-805"></span><span id="anchor-806"></span><span id="anchor-805"></span><span id="anchor-807"></span><span id="anchor-805"></span><span id="anchor-806"></span><span id="anchor-805"></span>Hidden LtK User

In *setup*, line 93 has a REMmed out line that Lt. Kernal SysOps might
be interested in.  If you unREM this line and move your boot disk files
to another user on your drive, you can boot from that user and the BBS
automatically switches back to user 0 during initialization.  This lets
Lt. Kernal SysOps "hide" their boot files on a normally unseen user and
boot the BBS as normal.

### <span id="anchor-809"></span><span id="anchor-810"></span><span id="anchor-809"></span><span id="anchor-811"></span><span id="anchor-809"></span><span id="anchor-810"></span><span id="anchor-809"></span><span id="anchor-812"></span><span id="anchor-809"></span><span id="anchor-810"></span><span id="anchor-809"></span><span id="anchor-811"></span><span id="anchor-809"></span><span id="anchor-810"></span><span id="anchor-809"></span>LtK Fast Blocks Free Read

In line 1081 of im, about ¼ of the way through the line, there is a
statement that looks like this:

*on-(dv%&lt;&gt;0)goto1083*

Changing the dv%&lt;&gt;0 to dv%&lt;&gt;8 tells the BBS you have a Lt.
Kernal running DOS v7.2 or higher set up as device 8.  This mod allows
the Lt. Kernal fast blocks free reads to be done on just the Lt. Kernal
and the standard routines for all other drives, thus allowing you to
easily mix a Lt. Kernal and standard serial drives without losing the
fast blocks free read on the Kernal.

For users of Lt. Kernal DOS v7.1 and earlier, do *not* change this line.
You can still access all of the LUs, but the fast blocks free read
routines will not work and will lock up your system.

### <span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span><span id="anchor-815"></span><span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span><span id="anchor-816"></span><span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span><span id="anchor-815"></span><span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span><span id="anchor-309"></span><span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span><span id="anchor-815"></span><span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span><span id="anchor-816"></span><span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span><span id="anchor-815"></span><span id="anchor-813"></span><span id="anchor-814"></span><span id="anchor-813"></span>Automatic CMD Device Clock Set

In *setup*, line 117 is REMed out.  It contains the hook for routines to
set the Image BBS system clock based on the CMD's internal clock.

### <span id="anchor-817"></span>Blocks Free Array Usage Change

The use of the *bf()* array has been changed.  There is no longer a need
to change the number of devices or drives when you add new drives to
your system.  With CMD systems, someone defining large numbers of
partitions would end up with almost no RAM free, so the array was cut
down to only include the system disks.

### <span id="anchor-818"></span><span id="anchor-819"></span><span id="anchor-818"></span><span id="anchor-820"></span><span id="anchor-818"></span><span id="anchor-819"></span><span id="anchor-818"></span><span id="anchor-821"></span><span id="anchor-818"></span><span id="anchor-819"></span><span id="anchor-818"></span><span id="anchor-820"></span><span id="anchor-818"></span><span id="anchor-819"></span><span id="anchor-818"></span>Enabling Macros

If you have Macros defined and would like them to come up automatically,
simply add the following to the end of line 82 in *setup*:

*:&,52,21,1*

### <span id="anchor-822"></span>R<span id="anchor-823"></span><span id="anchor-822"></span>Removing Extra Login Security Checks

From Marc Honey:

One thing that really annoys me is the extra security checks after
entering your login id and password. To get rid of those extra checks
all you have to do is remove the following lines from the +.lo file on
the Plus Disk.

*673 &"Additional Information:":a=int(rnd(1)\*5)+1:on a goto
675,676,677,678*

*674 p\$="FIRST name ":t\$=ff\$:goto679*

*675 p\$="LAST name ":t\$=ll\$:goto679*

*676 p\$="AREA CODE (???)XXX-YYYY ":t\$=mid\$(ph\$,2,3):goto679*

*677 p\$="DIALING PREFIX (XXX)/???-YYYY ":t\$=mid\$(ph\$,7,3):goto679*

*678 p\$="LAST FOUR DIGITS (XXX)/YYY-???? ":t\$=right\$(ph\$,4)*

**

<span id="anchor-824"></span>Change line 679
============================================

<span id="anchor-825"></span>from: *679 gosub1006:c\$=an\$:goto156*
===================================================================

to: *679 goto156*

<span id="anchor-826"></span>Change line 157
============================================

<span id="anchor-827"></span>from: *157 ifpw\$=z\$andt\$=c\$andz\$&lt;&gt;""andc\$&lt;&gt;""then160*
====================================================================================================

to: *157 ifpw\$=z\$andz\$&lt;&gt;””then160*

That’s all there is to it! As an added bonus, removing those few lines
will drop your +.lo file size from 40 blocks to 39 blocks and every
little bit helps on space and speed ;)

<span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span><span id="anchor-830"></span><span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span><span id="anchor-831"></span><span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span><span id="anchor-830"></span><span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span><span id="Troubleshooting"></span><span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span><span id="anchor-830"></span><span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span><span id="anchor-831"></span><span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span><span id="anchor-830"></span><span id="anchor-828"></span><span id="anchor-829"></span><span id="anchor-828"></span>Troubleshooting / Q & A
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Here are some of the most common questions and problems that people
have:

<span id="anchor-832"></span>**Q:** I load the program, and it never gets to the idle screen.  What is wrong?
=============================================================================================================

**A:** There are several things that could cause this.  Check all the
following:

1.  Has your BBS been properly and completely configured using the
    instructions in the setup chapter under CONFIG?
2.  Is each system disk in the correct device/drive?
3.  Are all the files copied to the correct system disks, especially the
    plus-file disk?  If an error light is flashing on any of the drives,
    it usually means that it cannot find a needed file.
4.  Are all disk units in proper alignment?
5.  Is everything connected to the computer (printers, drives, etc.)
    turned on?  Problems can arise if they aren’t, even if the BBS is
    not using them.
6.  The disk or disk image could be faulty.  Try re-copying or
    re-downloading it.

### <span id="anchor-833"></span><span id="anchor-299"></span><span id="anchor-833"></span>The Boot Process

*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\
\* The following article appeared in \*\
\* the May issue of \*\
\* "The Reflection" \*\
\* \*\
\* It is reproduced here for the \*\
\* benefit of any that may have \*\
\* missed it. It may be used as a \*\
\* text file on other boards provided \*\
\* it is used in it's entirety. \*\
\* \*\
\* "The Reflection" is available by \*\
\* subscription for \$15.00 per year \*\
\* from: \*\
\* Reflection \*\
\* P.O. Box 525 \*\
\* Salem, UT 84653 \*\
\* \*\
\* NOTE: Subscription price is subject \*\
\* to change without notice. \*\
\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*
*

*IN THE BEGINNING:\
By: Fred Dart (THE CHIEF)*

This month we'll take a look at the 'boot up' process and show what
files are accessed and in what order.

There has been a lot of confusion and thus a lot of questions about what
was happening and when, this should help a bit.

IMAGE is loaded by a “loader” program called *IMAGE*, *IMAGE 1.1*, or
*IMAGE 1.2* as appropriate. This loader program then loads the "ml"
(machine language) portion of the program, called simply, "ml", or "ml"
plus the appropriate version number. We will not continue to indicate
the various versions unless such designation is essential.

After the "ml" is loaded program control and execution is turned over to
that portion of the program, which in turn loads the file called
"screen", “im", and finally, "setup" (these files vary from version to
version with some additional "ml" routines loaded both before and after
"setup") and then program control is turned over to the BASIC portion of
the program by RUNning the "setup" program.

setup will "set up" all of the system variables, DIM all variables that
the system needs to operate and load additional files, if necessary, and
will then look for a file called "bd.data" which contains all of the
device and drive information for the system.

"bd.data" is a sequential file and can be on the boot disk, if there is
a separate boot disk, or on the disk that the system is booted from. If
the "bd.data" file is not found there will be a prompt to "INSERT ALL
SYSTEM DISKS".

If "bd.data" is found the program will next open the "u.config" file and
read the information from record one, the sysop information, which is
stored in the variables i1\$ and i2\$. On later versions the "u.index"
is then opened and the actual number of users is read. (Note that the
index is manipulated and read with the file "++ 4").

Following the "u.config" the file called "e.data", a relative file that
contains 31 or 32 records of 31 bytes each is accessed. The information
that is read in from "e.data" at this time is the total number of calls
to the system (record 1), the total number of users (record 12), the
total number of HANDLES in version 1.0, from record 16, the last user on
the system (d3\$) from record 17, the system password for password subs
(pp\$) from record 18,the last date/time the system was accessed in
record 19, whether there is a prime time and what the time limits are in
record 20, the information for the user FLAGS is read in from records 21
to 30, and the next id number to be assigned to a new user in record 31
(l1).

If the "bd.data", "u.config" or "e.data" files are not found on the
device and drive that they are assigned the system will prompt with the
same message, "INSERT ALL SYSTEM DISKS AND PRESS RETURN".

After the information has been read from "e.data" the relative file
"e.stats" is opened and the first 30 records are read. "e.stats"
contains the information shown on the BAR STATS and is a file consisting
of 38 records of 10 bytes each.

The program file "+.lo" is then loaded and program control is turned
over to that file. The "+.lo" file is a smaller file and cannot exceed
40 blocks, since it must load another file, the "+.modem" file, into a
protected area of memory reserved for "little modem files". The "little
modem files" are finding much more widespread use in the system than
just as modem files and are now being used in on-line games, such as
"Wallstreet" and in other areas of the board.

After the modem file is loaded it will send the proper set of commands
to the modem to prepare it to answer a call and then the board will go
to the "System Idle" screen and the load sequence will be completed.

Some additional information about a couple of the files here may be in
order. "bd.data" contains several important board parameters in addition
to the device/drive designations for all of the assigned system drives.
The information is stored sequentially, with the first 12 entries being
the devices/drives for the six system drives, (dr=1 through dr=6),
followed by the board identifier that you use on your board (LD, CH, TN
or whatever).

That is followed by the number of credits you give to new users when
they sign on the system, then by a number that represents the highest
device number you have attached to your system minus 7. For example, if
you are using devices 8, 9, 10, and 11 the number in field 15 would be a
4 (11-7). For a Lt. Kernal system using device 8 only the number is a 1.

The following number in field 16 is the number of DRIVES attached to
your system. If you have all 1541/71/81 types it would be a 1 since they
are all SINGLE drive units, if you had a Lt. Kernal with 9 LUs accessed
it would be a 9. The next field, number 17 contains your board name.
This is the information that is printed out with the MCI variable *£v5*
or the string bn\$.

The last information to be accessed is the prompt information, which is
read in and stored in po\$. The final line of *bd.data* contains the
copyright information.

The information contained in "e.data" is detailed above for the most
part, since most of it is accessed. There is some that is not accessed
by "setup" though and is not read in until it is needed. We'll examine,
briefly, some of the other information in "e.data". Record one, as
stated, is the total number of calls to the system. Records two through
11 are the names of the access groups, from "New User" to "Sysop" or
whatever names you have on yours. In addition to the NAME of the group
there is a bit of information

attached to the very beginning of the name. The first character of the
name of each group contains some access information that is stored in
bits.

This information is the calls per day, time per call, minutes allowed to
idle and so on. If you simply TYPE the "e.data" on a Lt. Kernal the
first character could appear as a color or some other strange character,
the program "edata edit" properly interprets the characters and can be
used to view the entries, "+.access" or the off-line "config" program
should be used for editing.

Record 12 is the total number of users plus 1.

Records 13, 14 and 15 contain the flags for whether your individual
message bases, UD libraries, or UX libraries are open or closed. If all
are open then the three records would contain 30 zeros each, if any were
closed there would be a one in the position corresponding to the closed
board.

Record 16 contains the total number of handles you have on version 1.0.
It is not used on the enhanced versions.

Record 17 is the handle of the last user on the system.

Record 18 the password for the password subs.

Record 19 is the date/time the last user signed off.

Record 20 is for prime time: whether you have a prime time and, if so,
the start and end times. The information is stored as three numbers
separated by commas. For example: 0, 0, 0 is no prime time, of course.
If the first number is not a 0 it would indicate that you had a prime
time, the second number would be the start time and the third number
would be the end time. The variables pt%, p1%, p2% and p3% are used.

Records 21 through 31 have been covered previously.

Record 32 is used to hold the modem string, a string of seven characters
with the information for each individual modem on version 1.2.

In addition version 1.3 will contain some new data in the "e.data" file.
More information will be available later.

"u.config" contains all of the user data and will not be covered here.

There is one additional bit of information that is worth mentioning in
the *setup* file. Many people have asked where the message "Entering
Chat Mode" or "Exiting Chat Mode" is stored. The information is put in
c1\$, c2\$ and c3\$ during the boot process and remains there. It can be
changed in setup if desired.

An additional "tidbit" for the enhanced version is the location of the
password mask. The location is 17138 and can be 'poked' with about any
printable character, just decide what character you want, say a "?" for
example, use the statement print asc("?") and it would print out the
number 63. You would then poke that value into 17138 and change the
password mask from an X to a ?.

Note that you could also use this: poke17138,asc("?") and achieve the
same results. It is even possible to 'randomize' the password mask by
adding the poke in "+.lo" and having it poke a random value from a
string of acceptable characters.

\(c) May 1990 FandF Products

Permission to reprint is granted provided the file is printed in it's
entirety.

**I*f you want physical 1541/1571/1581 disks sent through postal mail,
please send an e-mail to sym\_rsherwood@yahoo.com, specifying the
format(s).  We'll make arrangements regarding shipping cost—not that
it'll be much.  My goal is not to make money off this—unless you want to
donate some—but see a revival of one of the top Commodore 64 BBSes into
common usage again.*

**Q: **As reported by Ray "The Wiz" LeJuez: the bootup process seems to
freeze with his C128D in C64 mode, after the message

<span id="anchor-834"></span>***Reading System Configuration...***
==================================================================

The internal 1571 drive is set to device \#8, his Lt. Kernal HD is
device \#10.

*bd.data* devices/drives were set for device 10, drive 0.

**A: **There is some speculation that a modification to the Lt. Kernal
HD for burst mode in 128 mode may have caused the problem; it boots to
the "waiting for call" screen just fine on his C64.

<span id="anchor-835"></span>**Q:** My users cannot log on or send e-mail using the handle.  Using the ID number works fine.  Why?
==================================================================================================================================

**A:** Files can sometimes get corrupted by what we call an "act of God"
(why does He always get blamed for this stuff?).  A power
brownout/blackout, surge, etc. during a write can do nasty things like
this.

This particular problem is caused by the *u.config* file being
corrupted.  Run *+.alpha/ind*, and it should clear things up.  (This
program can take quite a while to run, especially if you have a lot of
users, so be patient here!)

Select the options in the following order: LOAD, CLEAR, MAKE, SAVE.  The
*u.index* file will be re-generated.

*Notice as the list is created, it shows what alphabetical position the
user is in for the u.index file; this has no bearing on the user's BBS
ID number.  Also, a bit of debugging information (the a% and b% values,
used in the call to the indexer) is shown.*

<span id="anchor-836"></span>Notes About Users
----------------------------------------------

From Marc Honey:

*If for some reason you find yourself with a corrupted *u.config* file
(where the users are stored) and have to re-create one from scratch,
don’t forget to edit the *e.data* file to reset both the user count and
the next available user \#. If you don’t do this then someone can login
and type a user \# that was previously assigned but no longer exists.
When this happens the person logging in will get a password prompt but
once they type in a password and hit enter the BBS will lock-up. Another
odd side effect of not updating the *e.data* file is that should someone
login as NEW they will get id 0 for their login id which is invalid.
There is a basic program called *edata edit* which is on disk \#2 of the
image 1.2a BBS distro.*

If this still does not remedy the situation, go into ED and see if user
information is still correct.  If not, contact Pinacolada for help.  He
is working on (as of 1/2008) a user file backup/restore program; after
losing half his users' information due to random binary garbage in the
user file, he vowed that would never happen again.

**Q:** My BBS has started to do (any number of strange things) it was
not doing before.  What is wrong? *This question gets asked frequently
during beta-testing.*

**A:** This is usually caused by *some* modification that has been made
to the BBS or a plus-file module.  It may not show up for *days* after a
modification has been made, so the problem may not be readily apparent.
The fix is to:

-   Copy the original file in question over from your back-up copy of
    IMAGE BBS, or previous system file(s) you were running
-   Isolate which file the problem is in, perhaps using the "IMAGE Mod
    Maker"
-   Correct the error, or notify the program maintainer, if there
    is one.

Also, have you added anything new (hardware, a new game plus file) to
your BBS recently?  What has changed since the problem started? Many
times, some of the smallest changes can create the largest problems.

<span id="anchor-837"></span>**Q:** My modem (or telnet bridge device) will not work correctly.  What can I do?
===============================================================================================================

**A:** First of all, *don't panic*. (Apologies to the late, great
Douglas Adams.)  Seriously... since the advent of Rascal's *e.modrc* fix
which adds a configurable modem initialization string and the ability to
customize modem response codes, there are many more options to consider
than in the old days.

Plus, if you're running a telnet BBS with a bridge program, there are
additional things to consider, some of which I will touch upon in

-   DCD carrier detect options in tcpser

If you have a Supra 2400 baud modem, you will need to set it up
specially before you put it on line.  Run the *2400 setup* program on
the IMAGE disk with the modem on-line and turned on, and then boot your
IMAGE BBS!

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<span id="anchor-838"></span><span id="anchor-839"></span><span id="anchor-838"></span><span id="anchor-840"></span><span id="anchor-838"></span><span id="anchor-839"></span><span id="anchor-838"></span>Index
================================================================================================================================================================================================================

- A -

<span id="anchor-841"></span>Access codes.................................................6, 17
===============================================================================================

Access groups................................................7, 18

changing................................................12

AutoMaint.......................................................

  - B -

<span id="anchor-842"></span>B.A.R. screen...........................................11, 19, 21
===============================================================================================

BBS listings.................................................35-36

Bells, local....................................................13

Booting.....................................................10, 55

boot disk................................................4

- C -

<span id="anchor-843"></span>Cartridges.......................................................2
===============================================================================================

Chat....................................................12, 13, 20

message.............................................14, 20

Check line..........................................See "lightbar"

Clock...........................................................11

Color/Graphics mode.....................................12, 14, 22

Command stacking................................................22

Configuring..............................................5, 17, 50

Conversion, 12.0-12.1.........................................8, 9

Copier..........................................................48

offline ("copy-all" or "rel copy")........................

on-line ("CP" command)....................................

protocol..................................................

Copyright message...............................................14

Credits..........................................................8

adding to a user..........................................

ratios..................................................18

unlimited...............................................19

when validating/unvalidating files........................

- D -

<span id="anchor-844"></span>Debugging.......................................................12
===============================================================================================

Deleting users..............................................48, 50

Devices/drives...................................1, 2, 4, 5, 6, 10

blocks free.........................................11, 14

changing number..........................................2

hard drives.......................................1, 5, 56

directories..............................................3

- E -

<span id="anchor-845"></span>Editing parameters..............................................21
===============================================================================================

Editing users...................................................47

Editor (see also MCI)........................................39-45

commands.............................................39-41

abort...................................................39

border..................................................41

columns.................................................41

clear text..............................................41

delete..................................................40

edit....................................................40

Editor (see also MCI)........................................39-45

exit....................................................40

get files...............................................41

find....................................................41

help....................................................41

insert..................................................40

justify.................................................40

line numbering..........................................40

== PAGE 58 \* INDEX ==

list....................................................40

  MCI read................................................40

put file................................................41

read....................................................40

save....................................................39

view disk directory.....................................41

control keys............................................41

line ranges.............................................39

MCI commands.........................................42-45

number of lines available...............................18

e-mail....................................................16, 30-31

access to...............................................19

forced e-mail.............................................31

reading email...........................................30

sending email...........................................30

Error log.......................................................49

Expert mode.....................................................22

- F -

<span id="anchor-846"></span>Feedback........................................................20
===============================================================================================

viewing.................................................49

- G -

<span id="anchor-847"></span>Garbage collection..............................................14
===============================================================================================

Graffiti........................................................16

- H -

<span id="anchor-848"></span>Handles......................................................8, 55
===============================================================================================

Help menus......................................................20

Hotkeys.........................................................

- I -

<span id="anchor-849"></span>Idle screen.....................................................10
===============================================================================================

commands................................................

bottom screen...........................................13

  top screen..............................................11

Instant logon...................................................14

Interfaces.......................................................2

Printer..................................................

<span id="anchor-850"></span>RS232....................................................
======================================================================================

- K -

<span id="anchor-851"></span>Keeping e-mail
===========================================

in selective delete.......................................

<span id="anchor-852"></span>Killing
====================================

files in transfer libraries...............................

news files................................................

old posts.................................................

- L -

<span id="anchor-853"></span>Last call date change..........................................21
==============================================================================================

Lightbar (listed in order of appearance)

Sys....................................................12

Acs....................................................12

Loc....................................................12

Tsr....................................................

Cht....................................................

New....................................................

Prt....................................................

<span id="anchor-854"></span>U/D....................................................
====================================================================================

Asc....................................................

Ans....................................................

Exp....................................................

Fn5....................................................

Fn4....................................................

Fn3....................................................

Fn2....................................................

Fn1....................................................

Local mode..................................................12, 22

Log of callers..............................................19, 21

    printing....................................................13

    restarting..................................................50

Logical files....................................................2

Login indentifier................................................8

Logoff..........................................................20

Logon...........................................................14

instant.................................................14

restricting.............................................12

- M -

<span id="anchor-855"></span>Machine language routines.......................................54
===============================================================================================

Main command level..........................................16, 20

  prompt.........................................................8

maintenance..................................................47-50

  file..........................................................19

  remote........................................................19

  sub-board.................................................19, 25

== PAGE 59 \* INDEX ==

memory...................................................11, 3, 51

MCI commands.................................................42-45

access to...............................................19

commands.............................................42-45

abort...................................................45

about...................................................42

backspace...............................................43

bells...................................................42

clear screen............................................42

color...................................................42

numeric digit formatting................................45

get character...........................................42

input...................................................43

integer variable........................................45

jump on equal...........................................43

jump on not equal.......................................42

  "kolorific".............................................43

  leading characters......................................45

  new lines...............................................43

  "over" (repeat character)...............................43

  printer mode............................................43

  print modes.........................................43, 44

  print speed.............................................44

  reset defaults..........................................44

  reverse mode............................................44

  string variables........................................45

  tab.....................................................45

  test variables..........................................44

  variables...............................................44

  wait....................................................44

Modems........................................................1, 4

answering manually......................................11

carrier detect..........................................12

carrier invert..........................................11

files (modules).......................................1, 4

resetting...............................................11

speaker on/off..........................................11

supported...............................................

Supra 2400..............................................56

troubleshooting/setup...................................56

Movie files...............................................3, 33-34

- N -

NetMaint..........................................................

Networking........................................................

planning a network........................................

utilities.................................................

New users................................................7, 12, 15

credits..................................................8

viewing information.....................................49

New user

message.................................................22

restrictions..............................................

viewing in VF.............................................

News files......................................................32

At login..................................................

Adding....................................................

Editing...................................................

Killing...................................................

- O -

<span id="anchor-856"></span>Output routine.................................................53
==============================================================================================

- P -

Passwords...................................................8, 22

Plus files.................................3, 4, 33-34, 49, 51-53

Prime time................................................8,13,19

Printers........................................................2

MCI command............................................43

printing log...........................................13

printing on-line.......................................13

routines used............................................

supported types..........................................

private system.................................................13

programming................................................51, 54

prompt mode....................................................21

pseudo-local mode..........................................12, 18

- Q -

<span id="anchor-857"></span>Quitting to main command prompt................................21
==============================================================================================

- R -

<span id="anchor-858"></span>Reconfiguring................................................9, 50
===============================================================================================

RAM Expansion Units..............................................2

RES accounts............................................15, 48, 50

- S -

Screen

files (scn.\*).............................................

files (user text).........................................

logon...................................................15

Screen blanking.................................................13

Serial number...................................................14

changing....................................................

Setting time....................................................10

manually..................................................

reading real-time clocks..................................

Status report...................................................21

Subsystems, changing............................................22

Sub-boards.............................................5, 6, 23-25

ability to post/respond.................................18

anonymous boards.....................................6, 25

defining sub-boards..................................6, 17

editing/killing bulletins...............................24

frozen bulletins........................................25

non-anonymous boards.................................6, 25

password boards..................................6, 25, 48

posting bulletins.......................................24

reading bulletins....................................23,24

Subops/co-sysops..........................................6, 7, 25

Subroutines..................................................51-52

Sysop account....................................................7

System files..................................................2, 3

d.\* files................................................3

e.\* files................................................3

m.\* files................................................3

s.\* files........................................3, 16, 17

u.\* files................................................3

+.\* files.............................................3, 4

System information..............................................20

Sayings (SY)....................................................21

- T -

Telnet bridges

BBS Server................................................

defined...................................................

tcpser1.0rc12.............................................

tcpser4j..................................................

Terminal program............................................11, 46

phonebook...........................................16, 46

Text files...............................................4, 33, 34

Time on system..............................................13, 21

Total calls.................................................... 14

Trace.......................................................... 12

- U -

<span id="anchor-859"></span>Upload/download........................................5, 6, 26-29
===============================================================================================

copying/moving files................................28, 29

defining libraries...................................6, 17

exchange libraries......................................29

file transfers......................................26, 27

free download libraries..............................6, 29

killing files...........................................28

protocols...............................................26

reading files...........................................28

restricting......................................3, 17, 19

subops..................................................28

validating/unvalidating files...........................28

User flags............................................7, 18, 47-48

User information................................................15

User list...................................................19, 38

- V -

<span id="anchor-860"></span>Validating files................................................28
===============================================================================================

Variables....................................................51-53

variable list...................................................53

Voting booth....................................................37

- W -

Weeding old users.................................................

non-weed flag...........................................18

Windows (transmit/receive)......................................14

WF (SEQ file editor).....................................17, 48-49

[^1]:  In My Humble Opinion

[^2]:  Source for RS232/EIA232F terminology: *Data Communications: A
    Business User's Approach*, Fourth Edition, p. 120.  Also, Rascal's
    excellent dissertation of modem terminology included with his
    "e.modrc" fix.

[^3]:  American Standard for Computer Information Interchange

[^4]:  shorthand for the American National Standards Institute Standard
    X3.64

[^5]:  a misleading name, since it doesn't automate anything as the MX
    or MACS user commands do

[^6]:  in ANSI graphics or Commodore 128 80-column mode:£C8: dark
    purple, £CK: dark cyan