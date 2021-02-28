# -*- coding: utf-8 -*-
"""
PIE bot

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

"""

import codecs
import re
import random
import argparse
import json

dPIECleanMap = {'n':'n','m':'m','l':'l','r':'r\\','w':'w','y':'j','H':'\H','g':'g',\
            's':'s','ǵ':'g_>','gw':'gw','d':'d','b':'b','ḱ':'k_>',\
            'kw':'kw','k':'k','p':'p','t':'t','h1':'h1','h2':'h2','h3':'h3',\
            'e':'e','u':'u','i':'i','o':'o','(':'',')':'','a':'a',\
            'ǵh':'g_>h','gwh':'gwh','dh':'dh','bh':'bh','ḱh':'k',\
            'kwh':'kw','kh':'k','ph':'p','th':'t'}

dPhoneSet = set(dPIECleanMap.values())

PHONE_PATTERN = '|'.join(sorted([p.replace('(','\(').replace(')','\)') \
                                            for p in dPIECleanMap],\
                                            key = len,reverse=True))
phone_pattern = re.compile(PHONE_PATTERN)

# Read in PIE roots
pie_roots = json.load(codecs.open('PIE_roots_dict.json'))

xsampa_pie_roots = {}
for pie_root in pie_roots:
    xsampa_pie_roots[pie_roots[pie_root]["pron"]] = pie_root

english_roots = {}
for pie_root in pie_roots:
    english_roots[pie_roots[pie_root]["meaning"]] = pie_root

# Read in PIE suffixes
def read_in_pie_suffixes():
    """Reads the PIE suffixes file."""
    pie_suff_dict = {}
    for line in codecs.open('PIE_suffixes.txt'):
        [suff,meaning] = line.strip().split(None,1)
        pron = ' '.join(suff)
        pron = pron.replace('r','r\\')
        pie_suff_dict[suff] = {'meaning':meaning,'pron':pron}
    return pie_suff_dict

# Read in Spelling Model
spelling_model = json.load(codecs.open('p2g_model.json'))

def pron_breaker(pron):
    """Breaks pronunciations into chunks for spelling generation."""
    if len(pron) == 1:
        yield [pron]
    for i in range(1, len(pron)):
        start = pron[0:i]
        end = pron[i:]
        yield [start, end]
        for split in pron_breaker(end):
            result = [start]
            result.extend(split)
            yield result

sampa_map = {'e':'eI','u:':'u','a:':'A','iu':'ju','au':'aU','io':'IO','eu':'ju',
             'o:':'o','i:':'i','e:':'E','a':'A','ae':'eI'}


xsampa2ipa = json.load(codecs.open('xsampa2ipa.json'))

def generate_spelling(pron, final_e):
    """Generates a reasonable Modern English spelling from a pronunciation,
    based on the previously generated p2g model."""
    ## P2G model structure:
    ## {<phone_sequence>:{<letter_sequence>:count, <letter_sequence>:count...}}
    ## Algorithm: look up the phone string and subsets of the string to find
    ##  potential spellings. If all n phones are not in your model, back off to
    ##  n-1 phones and so on. Eg:
    ##   - For sequence ABCD, first see if ABCD is in the model. If not, look
    ##     for ABC and D, AB and CD, AB and C and D, and so on. You can output
    ##     all these potential spellings ranked by how many ngrams they contain
    ##     (fewer is better) multiplied by the counts in the model
    ##     (more is better).
    ##   - If the output sequence is discontinuous, i.e. with silent “e”, just
    ##     hold the “e” in abeyance until you can stick it in the right place
    ##     later. (The right place is after the next consonant group.)
    ## For each way of breaking up the pron, see if you have spelling coverage,
    ##  and give it a score
    spellings = []
    pron = [sampa_map[p] if p in sampa_map else p for p in pron]
    combinations = list(pron_breaker(pron))
    for broken_pron in combinations:
        #print(broken_pron)
        if False in [''.join(phone_seq_list) in spelling_model
                     for phone_seq_list in broken_pron]:
            continue

        phone_seqs = []
        for phone_seq_list in broken_pron:
            phone_seq = ''.join(phone_seq_list)
            #print('phone_seq',phone_seq)
            phone_seqs.append(sorted([(sp, spelling_model[''.join(phone_seq)][sp])
                                      for sp in spelling_model[phone_seq]],
                                     reverse=True,
                                     key=lambda x: x[1])[0])
            #print('phone_seqs',phone_seqs)
        spelling_score = float(sum([p[1] for p in phone_seqs]))/float(len(broken_pron))
        #print('spelling score',spelling_score)
        #print(''.join([l[0] for l in phone_seqs]))
        new_spelling = ''.join([l[0] for l in phone_seqs])
        if new_spelling[-1] in ['w','r','l','m','n'] and \
           new_spelling[-2] not in ['a','e','i','o','u','y']:
            new_spelling = new_spelling[:-1]+'e'+new_spelling[-1]
        if final_e and new_spelling[-1] != 'e':
            new_spelling = new_spelling+'e'
        spellings.append((new_spelling,spelling_score))


    ## Return the top 5 spellings
    top_five = [x[0] for x in sorted(spellings,reverse=True,key=lambda x: x[1])[:5]]
    #print(top_five)
    return top_five

# Pronunciation Mapping Sets

voiceless = ['p','t','k','f','T','x','kw']
VOICELESS_PATTERN = '('+'|'.join(sorted(voiceless,key=len,reverse=True)) + ')'
VOICED_PATTERN = '[^('+')|('.join(sorted(voiceless,key=len,reverse=True)) + ')]'
vowels = ['a','e','i','o','u','a:','e:','i:','o:','u:','y','y:','oe','oe:',\
              'E','E:','A','A:','O','O:','ae','ae:',\
              'eI', 'ai', 'oi', 'eu', 'au', 'ou',\
              'eI:', 'ai:', 'oi:', 'eu:', 'au:', 'ou:']
VOWEL_PATTERN = '('+ '|'.join(sorted(vowels,key=len,reverse=True)) +')'
CONSONANT_PATTERN = '[^('+')|('.join(sorted(vowels,key=len,reverse=True)) + ')]'

def sound_change(orig_pron, phone_maps, prior_context, posterior_context):
    """General function for conditioned sound changes."""
    # orig_pron is a list of phones
    # phone_maps is a dictionary of all the changes that occur in the context
    # prior/posterior_context are regexp that are matched against the pron
    prior_pattern = re.compile(prior_context)
    posterior_pattern = re.compile(posterior_context)
    new_pron = []
    for count,_ in enumerate(orig_pron):
        if orig_pron[count] not in phone_maps:
            new_pron.append(orig_pron[count])
            continue
        prior_phones = ' '.join(orig_pron[:count])
        posterior_phones = ' '.join(orig_pron[count+1:])
        if prior_pattern.search(prior_phones) and \
                posterior_pattern.search(posterior_phones):
            new_pron.append(phone_maps[orig_pron[count]])
        else:
            new_pron.append(orig_pron[count])
    return [count for count in new_pron if count != '']

def late_pie_changes(pron):
    """Laryngeal Deletion"""
    dict_h_deletion = {'h1':'','h2':'','h3':'','\H':''}
    late_pie_pron = [phone for phone in pron if phone not in dict_h_deletion]
    return late_pie_pron

def grimm_changes(pron):
    """Grimm's Law"""
    dict_grimm1 = {'p':'f','t':'T','k_>':'x','k':'x','kw':'xw'}
    dict_grimm2 = {'b':'p','d':'t','g_>':'k','g':'k','gw':'kw'}
    dict_grimm3 = {'bh':'v','dh':'D', 'g_>h':'G','gh':'G', 'gwh':'Gw'}

    # Grimm 1 applies everywhere except following 's'
    grimm_pron = sound_change(pron,dict_grimm1,'(.*[^s]|^$)','.*')
    grimm_pron = sound_change(grimm_pron,dict_grimm2,'.*','.*')
    grimm_pron = sound_change(grimm_pron,dict_grimm3,'.*','.*')

    return grimm_pron

def proto_germanic_changes(pron):
    """Proto-Germanic changes"""
    # o > a
    pg_pron = sound_change(pron,{'o':'a'},'.*','.*')

    # u > o if followed by nasal and then consonant
    pg_pron = sound_change(pg_pron,{'u':'o'},'.*','^(n|m) '+ CONSONANT_PATTERN)

    # e > i if followed by nasal and then consonant
    pg_pron = sound_change(pg_pron,{'e':'i'},'.*','^(n|m) '+ CONSONANT_PATTERN)

    # e > i if vowel in next syllable is i, i:, or has j
    pg_pron = sound_change(pg_pron,{'e':'i'},'.*','.*(i|i:|j)')

    # a: > o: everywhere
    pg_pron = sound_change(pg_pron,{'a:':'o:'},'.*','.*')

    # a > a: before n x; n and x deleted
    # this requires different machinery because of the deletion
    pg_pron = ' '.join(pg_pron).replace('a n x','a:').split()

    # i deleted after e:
    pg_pron = sound_change(pg_pron,{'i':''},'e:$','.*')

    # long dipthongs become short
    pg_pron = sound_change(pg_pron,{'eI:':'eI', 'ai:':'ai', 'oi:':'oi', \
                                        'eu:':'eu', 'au:':'au', 'ou:':'ou'},\
                               '.*','.*')

    # oi > ai, ou > au, ei > i:
    pg_pron = sound_change(pg_pron,{'oi':'ai','ou':'au','eI':'i:'},'.*','.*')

    # eu > iu before i,i:,j in next syllable
    pg_pron = sound_change(pg_pron,{'eu':'iu'},'.*','.*(i|i:|j)')

    return pg_pron

def old_english_changes(pron):
    """Old English changes"""

    # Gw > G before u
    oe_pron = sound_change(pron,{'Gw':'G'},'.*','^u')

    # Gw > w
    oe_pron = sound_change(oe_pron,{'Gw':'w'},'.*','.*')

    # G > j after i,j
    oe_pron = sound_change(oe_pron,{'G':'j'},'.*(i|i:|j)$','.*')

    # G > j before i,j
    oe_pron = sound_change(oe_pron,{'G':'j'},'.*','^(i|i:|j).*')

    # G > g initially
    oe_pron = sound_change(oe_pron,{'G':'g'}, '^$','.*')

    # G > g after n
    oe_pron = sound_change(oe_pron,{'G':'g'}, '.*n$','.*')

    # G > x finally
    oe_pron = sound_change(oe_pron,{'G':'x'},'.*','^$')

    # v > b initially
    oe_pron = sound_change(oe_pron,{'v':'b'},'^$','.*')

    # v > f finally, if after voiceless sound
    oe_pron = sound_change(oe_pron,{'v':'f'},'.*'+VOICELESS_PATTERN+'$','^$')

    # v > f between voiceless sounds
    oe_pron = sound_change(oe_pron,{'v':'f'},'.*'+VOICELESS_PATTERN+'$',\
                               '^'+VOICELESS_PATTERN+'.*')

    # D > d everywhere
    oe_pron = sound_change(oe_pron,{'D':'d'},'.*','.*')

    # x > h except finally or before voiceless
    oe_pron = sound_change(oe_pron,{'x':'h'},'.*','^'+VOICED_PATTERN)

    # h disappears between vowels
    oe_pron = sound_change(oe_pron,{'h':''},VOWEL_PATTERN+'$','^'+VOWEL_PATTERN)

    # z > r or 0
    oe_pron = sound_change(oe_pron,{'z':'r\\'},VOWEL_PATTERN+'$','.*')
    oe_pron = sound_change(oe_pron,{'z':''},CONSONANT_PATTERN+'$','^$')

    # a > ae (ash) EXCEPT before n or a following syllable with a, o, u
    # the rule below overgenerates but the alternative is pretty complex I think
    oe_pron = sound_change(oe_pron,{'a':'ae'},'.*','^[^naou]+$')

    # a: > o:
    oe_pron = sound_change(oe_pron,{'a:':'o:'},'.*','.*')

    # ai > a:, au > ea:, eu > eo:, iu > eo:
    oe_pron = sound_change(oe_pron,{'ai':'a:', 'au':'ea','eu':'eo:','iu':'eo:'},\
                               '.*','.*')

    return oe_pron

def late_old_english_changes(pron):
    """Late Old English changes"""
    # palatal umlaut
    # a range of vowels change prior to syllables with i, j
    loe_pron = sound_change(pron,{'a':'e','ae':'e','o':'e','u':'y',\
                                  'a:':'ae:','o:':'e:','u:':'y:',\
                                  'ea':'ie','eo':'ie','io':'ie'},\
                            '.*','^'+CONSONANT_PATTERN+'.*[i|i:|j].*')

    # velar umlaut
    # e > eo, i > io before [vlr][aou]
    loe_pron = sound_change(loe_pron,{'e':'eo','i':'io'},'.*','^[vlr] [aou]')

    # breaking
    # i > io, e > eo, ae&a > ea, i:&io:>eo: before r+cons, l+cons, h, x +cons
    loe_pron = sound_change(loe_pron,{'i':'io', 'e':'eo', 'ae':'ea','a': 'ea', \
                                          'i:':'eo','io:':'eo:'},\
                                '.*','^[rlhx]'+CONSONANT_PATTERN)
    return loe_pron

def me_vowel_lengthening(pron):
    """Middle English Vowel Lengthening"""
    new_phone = []
    for count, phone in enumerate(pron):
        if count < len(pron)-2:
            if phone in vowels and pron[count+1] in ['r\\','l','m','n']\
                    and pron[count+2] in ['b','d','g'] and phone[-1] != ':':
                new_phone.append(pron[count]+':')
            else:
                new_phone.append(phone)
        else:
            new_phone.append(phone)
    return new_phone

def me_vowel_shortening(pron):
    """Middle English Vowel Shortening"""
    new_phone = []
    for count, phone in enumerate(pron):
        if count < len(pron)-2:
            if phone in vowels and pron[count+1] in ['s','f']\
                    and pron[count+2] == 't' and pron[count][-1] == ':':
                new_phone.append(pron[count][:-1])
            else:
                new_phone.append(phone)
        else:
            new_phone.append(phone)
    return new_phone

def me_second_lengthening(pron):
    """Middle English Second Lengthening"""
    new_phone = []
    two_syll_pattern = '.*'+VOWEL_PATTERN+'.* .*'+VOWEL_PATTERN
    if re.compile(two_syll_pattern).search(' '.join(pron)):
        if pron[-1] in vowels:
            found_first_vowel = False
            for phone in pron:
                if phone in vowels and not found_first_vowel:
                    found_first_vowel = True
                    if phone[-1] != ':':
                        new_phone.append(phone+':')
                    else:
                        new_phone.append(phone)
                else:
                    new_phone.append(phone)
            pron = new_phone[:-1]
    return pron

def me_diphthongization(pron):
    """Middle English Diphthongization"""

    # ae [jh] > ai, e [jh] > ei, i [hj] > i, o [jh] > oi, u [jh] > ui
    # o: [wG] > ou, i: [Gw] > iu, a [Gw] > au, e [Gw] > eu, u [Gw] > u
    dip_i = {'ae':'ai', 'e' : 'eI', 'i' : 'i', 'o' : 'oi', 'u' : 'ui' }
    dip_u = {'o':'ou','i':'iu','a':'au','e':'eu','u':'u'}
    new_phone = []
    phone = 0
    while phone in range(len(pron)):
        if phone == len(pron)-1:
            new_phone.append(pron[phone])
            phone += 1
            continue
        p_lookup = pron[phone]
        if p_lookup[-1] == ':':
            p_lookup = p_lookup[:-1]

        if p_lookup in dip_i and pron[phone+1] in ['j','h']:
            new_phone.append(dip_i[p_lookup])
            phone += 2
        elif p_lookup in dip_u and pron[phone+1] in ['G','w']:
            new_phone.append(dip_u[p_lookup])
            phone += 2
        else:
            new_phone.append(pron[phone])
            phone += 1
    return new_phone

def middle_english_changes(pron):
    """Changes in Middle English"""

    # y > i, ae > a
    me_pron = sound_change(pron,{'y':'i','ae':'a'},'.*','.*')

    # y: > i:, ae: > E:, a: > O:
    me_pron = sound_change(me_pron,{'y:':'i:','ae:':'E:','a:':'O:'},'.*','.*')

    # ea > a, eo > e, ie > i
    me_pron = sound_change(me_pron,{'ea':'a','eo':'e','ie':'i'},'.*','.*')

    # vowel lengthening
    # vowels lengthen in open syllables and before [rlnm][bdg]
    me_pron = me_vowel_lengthening(me_pron)

    # vowel shortening
    # vowels shorten before [sf]t
    me_pron = me_vowel_shortening(me_pron)

    # vowels in open second syllables are dropped,
    # and preceding vowel lengthened
    me_pron = me_second_lengthening(me_pron)

    # combinatory changes
    # e > a before r
    me_pron = sound_change(me_pron,{'e':'a'},'.*','^r')

    # e > i [Nn][kgdt]
    me_pron = sound_change(me_pron,{'e':'i'},'.*','^[Nn][kgdt]')

    # ri > ir after consonant
    if 'r\ i' in ' '.join(me_pron):
        mw_pron = ' '.join(me_pron).replace('r\ i','r\_i').split()
        mw_pron = ' '.join(sound_change(mw_pron,{'r\_i':'i_r\\'},\
                                            CONSONANT_PATTERN+'$','.*'))
        me_pron = mw_pron.replace('_',' ').split()

    # new dipthongs
    me_pron = me_diphthongization(me_pron)

    # sk_> > S
    me_pron = ' '.join(me_pron).replace('s k_>','s_k_>').split()
    me_pron = sound_change(me_pron,{'s_k_>':'tS'},'.*','.*')

    # k_> > tS, G > w
    me_pron = sound_change(me_pron,{'k_>':'tS','G':'w'},'.*','.*')

   # h deleted before l, r, n
    me_pron = sound_change(me_pron,{'h':''},'.*','^[lrn]')

   # xw > hw
    me_pron = sound_change(me_pron,{'x':'h'},'.*','^w')
    me_pron = sound_change(me_pron,{'xw':'w'},'.*','.*')

    return me_pron

def early_modern_english_changes(pron):
    """Changes in Early Modern English"""

    # short vowels
    # a > O: before l
    emod_pron = sound_change(pron,{'a':'O:'},'.*','^l.*')

    # a > ae elsewhere
    emod_pron = sound_change(emod_pron,{'a':'ae'},'.*','.*')

    # u > V except after initial [pfwb], or before final l,sh
    emod_pron = sound_change(emod_pron,{'u':'V'},'.*[pfwb]$','.*')
    emod_pron = sound_change(emod_pron,{'u':'V'},'.*','^[lS]$')

    # long vowels: the Great Vowel Shift!
    great_vowel_shift = {'i:':'aI','e:':'i','E:':'i','u':'au','oU':'u:',\
                             'O':'ou','A:':'ae','ae:':'eI'}
    emod_pron = sound_change(emod_pron,great_vowel_shift,'.*','.*')

    # dipthongs
    emod_pron = sound_change(emod_pron, {'ai':'eI','au':'O','iu':'ju',\
                                             'eu':'ju','Eu':'ju',\
                                             'Ou':'oU','ui':'OI'},'.*','.*')
    emod_pron = ' '.join(emod_pron).replace('iu','j u').replace('eu','j u')\
        .replace('Eu','j u').replace('ju','j u').split()

    # f, T, s, tS gain voicing in unstressed positions
    # (represented here as in the second syllable,
    #  after the second vowel if there is one)
    emod_pron = sound_change(emod_pron, {'f':'v','T':'D','s':'z','tS':'dZ'},\
                                 '.*'+VOWEL_PATTERN+'.* .*'+VOWEL_PATTERN+'.*','.*')

    # x becomes f after ae; deleted otherwise
    emod_pron = sound_change(emod_pron,{'x':'f'},'.*ae$','.*')
    emod_pron = sound_change(emod_pron,{'x':''},'.*','.*')

    # mb > m
    emod_pron = sound_change(emod_pron,{'b':''},'.*m$','.*')

    # assibilation of tj, dj, sj, zj
    emod_pron = ' '.join(emod_pron).replace('t j','tS ').split()
    emod_pron = ' '.join(emod_pron).replace('d j','dZ ').split()
    emod_pron = ' '.join(emod_pron).replace('s j','S ').split()
    emod_pron = ' '.join(emod_pron).replace('z j','Z ').split()

    # vowel reduction?
    new_pron = []
    found_first_vowel = False
    for phone in emod_pron:
        if phone not in vowels:
            new_pron.append(phone)
        else:
            if not found_first_vowel:
                new_pron.append(phone)
                found_first_vowel = True
            else:
                new_pron.append('@')
    emod_pron = new_pron

    # remove length markers on vowels
    emod_pron = [p.strip(':') if p in vowels else p for p in emod_pron]

    # other tweaks for legibility, etc.
    emod_pron = ' '.join(emod_pron).replace('kw','k w').split()
    emod_pron = ' '.join(emod_pron).replace('gw','g w').split()
    emod_pron = ['IO' if p == 'io' else p for p in emod_pron]

    return emod_pron

# Generates the history, cognates, pronunciation, spelling and meaning of a new English word
# If 'none' is given for token or suffix it generates a random one
def generate_entry(pie_token,pie_suffix):
    """Generates the history, cognates, pronunciation, spelling and meaning of
    a new English word. If 'none' is given for token or suffix it generates
    a random one."""

    pie_suffixes = read_in_pie_suffixes()
    if not pie_token:
        pie_token = random.choice(list(pie_roots.keys()))
    else:
        if pie_token not in pie_roots:
            if pie_token in xsampa_pie_roots:
                pie_token = xsampa_pie_roots[pie_token]
            elif pie_token in english_roots:
                pie_token = english_roots[pie_token]
            else:
                print("ERROR:",pie_token,"not found in PIE roots.")
                return ""
    if pie_suffix == 'random':
        pie_suffix = random.choice(list(pie_suffixes.keys()))

    if not pie_suffix:
        pie_word  = {'token':pie_token,
                     'pron':pie_roots[pie_token]['pron'],
                     'meaning':pie_roots[pie_token]['meaning']}
    else:
        pie_word  = {'token':pie_token+pie_suffix,
                     'pron':pie_roots[pie_token]['pron']+' '\
                     +pie_suffixes[pie_suffix]['pron'],
                     'meaning':pie_roots[pie_token]['meaning']+' + '\
                     +pie_suffixes[pie_suffix]['meaning']}

    pie_pron = pie_word['pron'].split()

    # Late PIE
    lpp = late_pie_changes(pie_pron)

    # Grimm's Law
    grimm_pron = grimm_changes(lpp)

    # Verner's Law
    verner_pron = sound_change(grimm_pron,{'s':'z','f':'v','x':'Z','xw':'Zw'},\
                                   '.*'+VOWEL_PATTERN+'.* .*','.*')

    # Proto Germanic Vowel Changes
    pg_pron = proto_germanic_changes(verner_pron)

    # Proto-Germanic to Old English
    oe_pron = old_english_changes(pg_pron)

    # Late Old English
    loe_pron = late_old_english_changes(oe_pron)
    final_e = False

    # Middle English
    me_pron = middle_english_changes(loe_pron)
    if me_pron[-1] in vowels:
        final_e = True

    # Early Modern English
    emod_pron = early_modern_english_changes(me_pron)

    # Spelling
    pie_word['spelling'] = generate_spelling(emod_pron,final_e)[0]
    pie_word['mode'] = emod_pron
    pie_word['pgmc'] = pg_pron
    pie_word['olde'] = oe_pron
    pie_word['mide'] = me_pron
    pie_word['modex'] = [xsampa2ipa[p] for p in emod_pron]
    pie_word['pgmcx'] = [xsampa2ipa[p] for p in pg_pron]
    pie_word['oldex'] = [xsampa2ipa[p] for p in oe_pron]
    pie_word['midex'] = [xsampa2ipa[p] for p in me_pron]

    return pie_word

def print_summary(pie_word_dict):
    """Prints a summary of a generated Modern English word, and its history."""
    summary = ''.join(pie_word_dict['spelling']) + ' |' + ''.join(pie_word_dict['modex']) + '|\n'
    summary += ' > '.join(['PIE '+pie_word_dict['token'],\
                             'PGmc '+''.join(pie_word_dict['pgmcx']),\
                             'OEng '+''.join(pie_word_dict['oldex']),\
                             'MiddleEng '+''.join(pie_word_dict['midex']) + '\n'])
    if 'cognates' in pie_word_dict:
        summary += ';'.join(pie_word_dict['cognates']) + '\n'
    summary += pie_word_dict['meaning'].title()
    print(summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Module for generating modern "+\
                                         "English derivatives from PIE roots")
    parser.add_argument('-r','--root',help='PIE root from which to generate '+\
                        'modern English derivation. If none provided, one '+\
                        'will be randomly chosen. May be provided as a space '+\
                        'delimited XSAMPA phone sequence.')
    parser.add_argument('-s','--suffix',help='PIE suffix from which to generate '+\
                        'modern English derivation. If the word "random" is '+\
                        'provided, a random suffix will be randomly chosen. '+\
                        'See PIE_suffixes.txt for list.')
    parser.add_argument('-a','--analysis',help='prints reports on PIE roots: '+\
                        'phone sets.',action="store_true",default=False)
    args = parser.parse_args()

    if args.analysis:
        print('reading in PIE roots & suffixes')
        pie_suffix_dict = read_in_pie_suffixes()

        pie_phones = set([])
        pgmc_phones = set([])
        olde_phones = set([])
        mide_phones = set([])
        mode_phones = set([])

        for root in pie_roots:
            print('root:',root)
            for suffix in pie_suffix_dict:
                entry = generate_entry(root,suffix)
                pie_phones = pie_phones.union(set(entry['pron']))
                pgmc_phones = pgmc_phones.union(set(entry['pgmc']))
                olde_phones = olde_phones.union(set(entry['olde']))
                mide_phones = mide_phones.union(set(entry['mide']))
                mode_phones = mode_phones.union(set(entry['mode']))
        # Phone sets for PIE, PGmc, OldE, MidE, ModE
        with codecs.open('phonesets.txt','w',encoding='utf-8') as phoneout:
            phoneout.write('PIE phones:\n')
            phoneout.write(','.join(pie_phones)+'\n')
            phoneout.write('PGmc phones:\n')
            phoneout.write(','.join(pgmc_phones)+'\n')
            phoneout.write('OldE phones:\n')
            phoneout.write(','.join(olde_phones)+'\n')
            phoneout.write('MidE phones:\n')
            phoneout.write(','.join(mide_phones)+'\n')
            phoneout.write('ModE phones:\n')
            phoneout.write(','.join(mode_phones)+'\n')

    else:
        entry = generate_entry(args.root,args.suffix)
        if entry != "":
            print_summary(entry)
