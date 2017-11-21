
# When adding a new filter/capability to expressions

Add to:

* Expression repr test
* Expressions not equal test
* Interface tests
* Engine tests

# Typing

Should avoid static typing?
The idea is to mimic Pandas to some extent, so attributes should be 'opportunistically' typed.
Check the design philosophy here...

Check with pandas:

* What happens if I try to apply different typed filters to the same column?
* What filters are available on all types vs .dt .str subsets?

Type issues should be rejected only if they cause clashes in simplification?
In the domain simplifier, keep track of types of constants used in expressions, by marking types in a dictionary by attribute name.
Create the dictionary at the top level (when called with types=None) and, pass through the tree to track.
If there are clashes, throw an error, e.g.:

* Ranges specified with datetimes and numbers
* Timezone-aware and -naive datetimes
* Strings and numeric
* Unorderable types with Gt(), Lt(), etc...
* In() can take a set of arbitrary datatypes, unless combined with Ge/Le
Pass to numeric simplifiers if possible, otherwise set logic... the trick here will be integers vs floats??

Further checking should be pushed back to the source side, when deciding whether a query can be run.

# Design ideas to consider

* Python the 'adult' programming language
* Options for filters and logic available in the SQL standard
* Options for filters and logic available in pandas

# Numeric edge cases

If a variable is integer, (x > 3) & (x < 4) evaluates to False.
This could arise due to a caching situation such as (x >= 3) and ~(x <= 0) and ~(x in [1, 2]).
If x is not known to be integral, the result will not be False, but will try to run a query for (0 < x < 1) | (1 < x < 2) | (2 < x < 3).

Perhaps it isn't common to filter on integers in this way?
Could also provide tools to reject these cases to be used as plugins on the remote side, but that is basically type checking.

Make an integer type optional by providing a filter (x is integer.
In the truth table setup, this would end up being applied to every combination, and any implementation guaranteeing successful True/False outcome computation would have to guarantee the same in order to be complete.
DataSet objects could have this as a default filter... but its probably easier to have an optional type.
In this case, have a general 'object' type (like pandas uses), which has a priority order when required:

* Numeric types assumed to be floats on (-inf, +inf) unless typed as integer/natural/etc).
* Datetimes will be processed as tz-naive or -aware unless there are clashes or a type is specified.

# Next steps

* Get the 'object' attribute working, enough to intelligently handle strings/floats/datetimes.
* Do some research on pandas/sql approaches to typing before making things complicated.
* Start building examples with simple datetime and id filters (numeric id may be an obvious integer/natural number use case).
