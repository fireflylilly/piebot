# piebot
A small program to convert Proto-Indo-European roots to their modern 
English descendants, using rules of sound change.
This module generates English words that do not exist, but might have.
Both pronunciation and spelling suggestions are offered, reflecting English’s
idiosyncratic orthography. The words often seem whimsical or odd, but in fact
are no stranger than many actual English words. The program is offered
as a tool for creators of alternate history or lost words and names.

Inputs:
 - JSON databases of PIE roots and affixes
 - Optional: roots and affixes to start with (if not provided, they are
    chosen at random)
 - Optional: meaning for the target word (if not provided, it is created
    from the root and affix)

Outputs:
 - A string summary of the generated word, its pronunciation, its spelling,
    and its etymology

usage: piebot.py [-h] [-r ROOT] [-s SUFFIX] [-n NEW]

Module for generating modern English derivatives from PIE roots

optional arguments:
  -h, --help            show this help message and exit
  -r ROOT, --root ROOT  PIE root from which to generate modern English derivation.
                        If none provided, one will be randomly chosen. May be
                        provided as a space delimited XSAMPA phone sequence.
  -s SUFFIX, --suffix SUFFIX
                        PIE suffix from which to generate modern English
                        derivation. If the word "random" is provided, a random
                        suffix will be randomly chosen. See PIE_suffixes.txt for
                        list.
  -n NEW, --new NEW     A new (i.e. not in the database) PIE root from which to
                        generate a modern English derivation. Should be provided
                        as a space-delimited ASCII sequence.
