# Case files — `/vision`

War stories behind the rules in `commands/vision.md`. Each heading is pointed to from its rule.

## The search list nobody could check

**A logged `/vision` test run, read from its `docs/vision.md`.** The market read ran three searches and wrote
them on one line. Below them sat a table of eight comparables and ten source links. Nothing said which search
verified which product, and two of the eight were named by no query at all. Whether a result page covered them,
or the run knew them already, could not be told from the file. Step 3b asks the run to confirm the read *"cites
real named products (not from memory)"*. With that file, the confirmation is an assertion.

**The bound that was proposed and declined (#252).** The first proposal copied `/architect`'s rule: one
search per comparable. A review of seven logged `/vision` runs found **1 to 4 searches per run**, so a bound
saves nothing. It would also cut the wrong search: two of the 4-search runs spent a query on something that was
not a comparable at all, what users complain about in the category. That is where a sharpening insight comes
from. `/architect`'s safeguard does not carry over either. A comparable left unchecked is visible; an insight
never found is not, because the exit criterion is still met, just by a weaker insight.

**The rule this earned.** Every search goes in `docs/vision.md` as one line: query · what it settled (the
comparables it verified, the insight it gave, or "nothing"). There is no count. A comparable named without a
search gets its own line saying where the name came from. Step 3b then checks the read's comparables name by
name against the list, so "not from memory" becomes something a reader can check. It is the same receipt
principle the playbook applies to companion reads (`MECHANISMS-ON-DEMAND.md` §Read receipt).

*Deliberately not changed:* the five-part north star. #252's item 2, splitting it around `/validate`'s kill
verdict, was declined by the owner. It would open a window where three of its five parts do not exist.
