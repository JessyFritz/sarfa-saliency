
Legal details
-------------

Fruit 2.2.1 Copyright 2004-2005 Fabien Letouzey.

Fruit may not be distributed as part of any software
package, service or web site without prior written permission from the
author.


UCI options
-----------

- "BookFile" (name, default book.bin)

Specifies the path to the book which should be used. Fruit includes two books: book.bin and book-varied.bin. If you choose the latter you will get more variety in opening play but from time to time unsound openings as well.

- "TimeAllocation" (percentage, default 100%)

Specifies the time management in a game. Higher values will result in a more aggressive time usage and more time spent in the opening, lower values to a conservative time usage and more time left on the clock in the endgame.

- "EGTB" (true/false, default true)

Enables the usage of Nalimov Endgame Tablebases in the search

- "EGTB Depth" (0-20 plies, default:8)

Defines the minimum remaining depth (distance to horizon) for using EGTBs. Lower values result in a more aggressive use of EGTBs but a significant slowdown in endgame positions (due to heave disk access). For analysis or fast  SCSI Drives one can choose lower values.

- "NullMove Pruning" (Always/Fail High/Never, default: Always)

"Always" actually means the usual conditions (not in check, etc ...).
"Fail High" adds the condition that the static evaluation fails high.
Never use "Never" (ever)! 

I expect that this option has little effect (assuming the first two
choices only).  I only added it because most engines do not use the
fail-high condition.

- "NullMove Reduction" (1-3 plies, default: 3)

3 is rather aggressive, especially in the endgame.  It seems better
than always using 2 though.  I have not experimented with adaptive
solutions.

- "Verification Search" (Always/Endgame/Never, default: Always)

This tries to solve some Zugzwang-related problems.  I expect it to
hardly have any effect in games.  The default value should be
sufficient for most-common Zugzwang situations.

- "Verification Reduction" (1-6 plies, default: 5)

5 guarantees that the cost of verification search is negligible in
most cases.  Of course it means Zugzwang problems need a lot of depth
to get solved, if ever!  With such a reduction, verification search is
similar to Vincent Diepeveen's "double null move".

- "History Pruning" (true/false, default: true)

Activates or deactivate the history pruning. Deactivation will result in a safer search but reduce depth and therefore hurt playing strength.

- "History Threshold" (percentage, default: 70%)

 Lower values are safer and higher values more aggressive in the pruning decision.

- "Extended Futility Pruning" (true/false, default: true)

Moves which are expected to fail low are pruned based on material considerations. It helps to reach more depth but introduces possible errors in the search. Overall it increases strength at all time controls considerably

- "Extended Futility Margin" (centipawns, default: 300)

Larger values prune less but will lead to fewer errors.

- evaluation options (percentage, default: 100%)

These options are evaluation-feature multipliers.  You can modify
Fruit's playing style to an extent or make Fruit weaker for instance
by setting "Material" to a low value.

"Material" is obvious.  It also includes the bishop-pair bonus.
"Piece Activity": piece placement and mobility.
"King Safety": mixed features related to the king during early phases
"Pawn Structure": all pawn-only features (not passed pawns).
"Passed Pawns": ... can you guess?

I think "Pawn Structure" is not an important parameter.
Who knows what you can obtain by playing with others?

- material options (percentage, default 100%)

These options set the material value of the different pieces. It is unlikely to gain much by changing them but who knows.

- contempt factor (centipawns, default: 0)

This is the value Fruit will assign to a draw (repetition, stalemate, perpetual, 50-move-rule). It is from Fruits viewpoint. With negative values Fruit will avoid draws with positive values it will seek draws. The bonus is constantly reduced when material comes off and 0 if all material is exchanged. 


History
-------

2004/03/17 Fruit 1.0, first stable release
------------------------------------------

Fruit was written in early 2003, then hibernated for many months.
I suddenly decided to remove some dust from it and release it after
seeing the great WBEC web site by Leo Dijksman!  Note that Fruit is
nowhere near ready to compete there because of the lack of xboard
support and opening book.  Note from the future: these limitations
seem not to be a problem anymore.

Fruit 1.0 is as close to the original program as possible, with the
main exception of added UCI-handling code (Fruit was using a private
protocol before).  It is a very incomplete program, released "as is",
before I start heavily modifying the code (for good or bad).

You can find a succinct description of some algorithms that Fruit uses
in the file "technical_10.txt" (don't expect much).


2004/06/04 Fruit 1.5, halfway through the code cleanup
------------------------------------------------------

In chronological order:

- added mobility in evaluation (makes Fruit play more actively)

- added drawish-material heuristics (makes Fruit look a bit less stupid
  in some dead-draw endgames)

- tweaked the piece/square tables (especially for knights)

- added time management (play easy moves more quickly, take more time
  when unsure)

- enabled the single-reply extension (to partly compensate for the lack
  of king safety)

- some speed up (but bear in mind mobility is a costly feature, when
  implemented in a straightforward way as I did)


2004/12/24 Fruit 2.0, the new departure
---------------------------------------

The main characteristic of Fruit 2.0 is the "completion" of the
evaluation function (addition of previously-missing major features).

In chronological order:

- separated passed-pawn evaluation from the pawn hash table,
  interaction with pieces can now be taken into account

- added a pawn-shelter penalty; with king placement this forms
  some sort of a simplistic king-safety feature

- added incremental move generation (Fruit was starting to be too slow
  for my taste)

- added futility and delta pruning (not tested in conjunction with
  history pruning and hence not activated by default)

- improved move ordering (bad captures are now postponed)

- added history pruning (not tested seriously at the time I write
  this yet enabled by default, I must be really dumb)

- cleaned up a large amount of code (IMO anyway), this should allow
  easier development in the future


2005/06/17 Fruit 2.1, the unexpected
------------------------------------

Unexpected because participation in the Massy tournament had not been
planned.  What you see is a picture of Fruit right in the middle of
development.  There may even be bugs (but this is a rumour)!

I have completed the eval "even more", not that it's ever complete
anyway.  I have to admit that I had always been too lazy to include
king attacks in previous versions.  However, some programs had fun
trashing Fruit 2.0 mercilessly in 20 moves, no doubt in order to make
me angry.  Now they should need at least 25 moves, don't bother me
again!

- added rook-on-open file bonus; thanks to Vincent Diepeveen for
  reminding me to add this.  Some games look less pathetic now.

- added pawn storms; they don't increase strength but they are so
  ridiculous that I was unable to deactivate them afterwards!

- added PV-node extensions (this is from Toga), e.g. extending
  recaptures only at PV nodes.  Not sure if these extensions help; if
  they do, we all need to recognise Thomas Gaksch's contribution to
  the community!

- added (small) king-attack bonus, the last *huge* hole in the eval;
  now only large holes remain, "be prepared" says he (to himself)!

- added history-pruning re-search; does not help in my blitz tests,
  but might at longer time control; it's also safer in theory,
  everybody else is using it and I was feeling lonely not doing like
  them.  OK, Tord told me that it helped in his programs ...

- added opening book (compatible with PolyGlot 1.3 ".bin" files)

- fixed hash-size UCI option, it should now be easy to configure using
  all interfaces (there used to be problems with Arena, entirely by my
  fault)


2005/09/29 Fruit 2.2

- added side-to-move bonus

- added extended futility pruning

- tuned history pruning

- minor tuning of different parameters

- added Chess960-Support

- added multi variation support

- added "searchmove" which allows you to include/exclude different moves from the analysis

- added contempt factor

- changed most parameters to accept changes even after initialisation. This should help with different GUIs and sometimes strange order of UCI-commands.

- first competitive opening book for Fruit


2005/10/29 Fruit 2.2.1

- added Tablebase support

- fixed book-ponder-bug in Chessbase

- fixed hardware protection


Known bugs
----------

Fruit always claims that CPU is 100% used.  This is apparently a
problem in the standard C libraries on Windows.  Mailbomb me if fixing
this would save lives (especially children)!  I prefer waiting for
late users to throw away Windows 95/98/ME before adding an
NT/2000/XP/... solution.