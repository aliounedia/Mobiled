#----------------------------------------------------------------------------#
#                                                                            #
#    Copyright (C) 2009 Department of Arts and Culture,                      #
#                       Republic of South Africa                             #
#    Contributer: Meraka Institute, CSIR                                     #
#    Author: Mark Zsilavecz                                                  #
#    Contact: mzsilavecz@csir.co.za                                          #
#                                                                            #
#    License:                                                                #
#    Redistribution and use in source and binary forms, with or without      #
#    modification, are permitted provided that the following conditions are  #
#    met:                                                                    #
#                                                                            #
#     * Redistributions of source code must retain the above copyright       #
#       notice, this list of conditions and disclaimer. <See COPYING file>   #
#                                                                            #
#     * Redistributions in binary form must reproduce the above copyright    #
#       notice, this list of conditions and disclaimer <See COPYING file>    #
#       in the documentation and/or other materials provided with the        #
#       distribution.                                                        #
#                                                                            #
#     * Neither the name of the Department of Arts and Culture nor the names #
#       of its contributors may be used to endorse or promote products       #
#       derived from this software without specific prior written permission.#
#----------------------------------------------------------------------------#


#    The docstrings in this module contain epytext markup: API               #
#    documentation  may be created by processing this file with epydoc:      #
#    http://epydoc.sf.net                                                    #

# -*- coding: iso-8859-15 -*-

def custom_init(node, results):
    if not results.has_key('LANGUAGE'):
        results['LANGUAGE'] = 'ENGLISH'
    if not results.has_key('ATTEMPTS'):
        results['ATTEMPTS'] = 0
    if not results.has_key('LAST_NODE'):
        results['LAST_NODE'] = ''

def custom_0_1(node, results):
    audio = {'ENG_SHORT':eng_0_1, 'ENG_LONG':eng_0_1_long, 
             'AFR_SHORT':afr_0_1, 'AFR_LONG':afr_0_1_long, 
             'SET_SHORT':set_0_1, 'SET_LONG':set_0_1_long}
    question_node(node, results, audio)
           
def custom_1_0(node, results):
    if node.getLastOption() == 'english':
        results['LANGUAGE'] = 'ENGLISH'
    elif node.getLastOption() == 'afrikaans':
        results['LANGUAGE'] = 'AFRIKAANS'
    elif node.getLastOption() == 'setswana':
        results['LANGUAGE'] = 'SETSWANA'
    
    audio = {'ENG_SHORT':eng_1_0, 'ENG_LONG':eng_1_0_long, 
             'AFR_SHORT':afr_1_0, 'AFR_LONG':afr_1_0_long, 
             'SET_SHORT':set_1_0, 'SET_LONG':set_1_0_long}
    question_node(node, results, audio)
     
def custom_1_1(node, results):
    #TODO: get schedule info and format response correctly
    if results['LAST_NODE'] == node.getName():
        results['ATTEMPTS'] += 1
    else:
        results['ATTEMPTS'] = 0
    
    if results['LANGUAGE'] == 'ENGLISH':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':eng_1_1}, 0)
    elif results['LANGUAGE'] == 'AFRIKAANS':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':afr_1_1}, 0)
    elif results['LANGUAGE'] == 'SETSWANA':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':set_1_1}, 0)
    
    results['LAST_NODE'] = node.getName()
        
def custom_1_2(node, results):
    audio = {'ENG_SHORT':eng_1_2, 'ENG_LONG':eng_1_2_long, 
             'AFR_SHORT':afr_1_2, 'AFR_LONG':afr_1_2_long, 
             'SET_SHORT':set_1_2, 'SET_LONG':set_1_2_long}
    question_node(node, results, audio)
        
def custom_1_3(node, results):
    audio = {'ENG_SHORT':eng_1_3, 'ENG_LONG':eng_1_3_long, 
             'AFR_SHORT':afr_1_3, 'AFR_LONG':afr_1_3_long, 
             'SET_SHORT':set_1_3, 'SET_LONG':set_1_3_long}
    question_node(node, results, audio)
   
def custom_1_4(node, results):
    if results['LANGUAGE'] == 'ENGLISH':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':eng_1_4}, 0)
        
    elif results['LANGUAGE'] == 'AFRIKAANS':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':afr_1_4}, 0)
        
    elif results['LANGUAGE'] == 'SETSWANA':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':set_1_4}, 0)
    
def custom_wrong_input(node, results):
    audio = {'ENG_SHORT':eng_0_2, 'ENG_LONG':eng_0_2_long, 
             'AFR_SHORT':afr_0_2, 'AFR_LONG':afr_0_2_long, 
             'SET_SHORT':set_0_2, 'SET_LONG':set_0_2_long}
    error_node(node, results, audio)
            
def custom_no_input(node, results):
    audio = {'ENG_SHORT':eng_0_3, 'ENG_LONG':eng_0_3_long, 
             'AFR_SHORT':afr_0_3, 'AFR_LONG':afr_0_3_long, 
             'SET_SHORT':set_0_3, 'SET_LONG':set_0_3_long}
    error_node(node, results, audio)
    
def custom_0_4(node, results):
    if results['LANGUAGE'] == 'ENGLISH':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':eng_0_4}, 0)
        
    elif results['LANGUAGE'] == 'AFRIKAANS':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':afr_0_4}, 0)
        
    elif results['LANGUAGE'] == 'SETSWANA':
        node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':set_0_4}, 0)
        
        
def get_schedule():
    """"""
    

def question_node(node, results, audio):
    if results['LAST_NODE'] == node.getName():
        results['ATTEMPTS'] += 1
    else:
        results['ATTEMPTS'] = 0
    
    if results['LANGUAGE'] == 'ENGLISH':
        if results['ATTEMPTS'] == 0:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['ENG_SHORT']}, 0)
        elif results['ATTEMPTS'] == 1:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['ENG_LONG']}, 0)
        
    elif results['LANGUAGE'] == 'AFRIKAANS':
        if results['ATTEMPTS'] == 0:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['AFR_SHORT']}, 0)
        elif results['ATTEMPTS'] == 1:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['AFR_LONG']}, 0)
        
    elif results['LANGUAGE'] == 'SETSWANA':
        if results['ATTEMPTS'] == 0:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['SET_SHORT']}, 0)
        elif results['ATTEMPTS'] == 1:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['SET_LONG']}, 0)
        
    results['LAST_NODE'] = node.getName()
    
def error_node(node, results, audio):
    if results['LANGUAGE'] == 'ENGLISH':
        if results['ATTEMPTS'] == 0:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['ENG_SHORT']}, 0)
        elif results['ATTEMPTS'] == 1:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['ENG_LONG']}, 0)
        elif results['ATTEMPTS'] == 2:
            node.removeAudio(0)
            node.addGoto('0_4_operator')
        
    elif results['LANGUAGE'] == 'AFRIKAANS':
        if results['ATTEMPTS'] == 0:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['AFR_SHORT']}, 0)
        elif results['ATTEMPTS'] == 1:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['AFR_LONG']}, 0)
        elif results['ATTEMPTS'] == 2:
            node.removeAudio(0)
            node.addGoto('0_4_operator')
        
    elif results['LANGUAGE'] == 'SETSWANA':
        if results['ATTEMPTS'] == 0:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['SET_SHORT']}, 0)
        elif results['ATTEMPTS'] == 1:
            node.addAudio({'SOURCE':'SRC_TEXT_DTMF', 'VALUE':audio['SET_LONG']}, 0)
        elif results['ATTEMPTS'] == 2:
            node.removeAudio(0)
            node.addGoto('0_4_operator')
    
# All the text that must be rendered.
eng_0_1 = 'Tshwane Electricity Services. Hello, Goei Môre, Dumela! To hear about loadshedding in English, say “English.” Vir inligting oor beurtkrag in Afrikaans, sê: "Afrikaans.” Go utlwa ka ga tsa loadshedding ka Setswana, e re “Setswana.”'
eng_0_1_long = 'To hear the loadshedding schedule in English, say “English” now. Om die beurtkragskedule in Afrikaans te hoor, sê nou: "Afrikaans." Go utlwa kaga dinako tsa loadshedding ka Setswana, e re “Setswana” jaanong.'
eng_0_2 = "I'm sorry, I didn't understand you."
eng_0_2_long = "I'm sorry, I still didn't understand you."
eng_0_3 = "I'm sorry, I still didn't understand you."
eng_0_3_long = "I'm sorry, I still didn't hear anything."
eng_0_4 = 'Congratulations! You managed to reach the operator!'
eng_1_0 = 'What suburb do you want the loadshedding schedule for?'
eng_1_0_long = 'If you need assistance from an operator, you can say “operator” at any time. I can tell you the loadshedding schedule for all of the suburbs of Tshwane. Say the name of the suburb now.'
eng_1_1 = '[Suburb] {(load = true) LS, (load = false) noLS}, today, [Date]. Tomorrow, [Suburb] {(load = true) LS, (load = false) noLS}. This schedule was updated at [Update Time], [Update Date].'
eng_1_2 = 'Do you want to hear that again?'
eng_1_2_long = 'If at any time you need assistance from an operator, you can say “operator.” Do you want to hear the loadshedding schedule for [suburb] again? Say “yes” or “no” now.'
eng_1_3 = 'Do you want to hear about another suburb?'
eng_1_3_long = 'If at any time you need assistance from an operator, you can say “operator.” Do you want to hear the loadshedding schedule for another suburb? Say “yes” or “no” now.' 
eng_1_4 = 'Thank you for calling the loadshedding line at Tshwane Electricity Services. '

afr_0_1 = eng_0_1
afr_0_1_long = eng_0_1_long
afr_0_2 = "Ek is jammer, ek het nie verstaan nie."
afr_0_2_long = "Jammer, ek verstaan steeds nie."
afr_0_3 = "Ek is jammer, ek het niks gehoor nie."
afr_0_3_long = "Jammer, ek hoor steeds niks nie."
afr_0_4 = "Veels geluk - ek skakel u deur na 'n agent!"
afr_1_0 = "Vir welke voorstad wil u die beurtkragskedule hoor?"
afr_1_0_long = "Indien u hulp van 'n diensagent benodig, kan u enige tyd 'agent' se^. Ek kan inligting verskaf oor al die voorstede van Tshwane. Se^ asseblief nou die naam van die voorstad."
afr_1_1 = "[Suburb] {(load = true) LS:vandag, (load = false) noLS} [Date]. [Suburb] {(load = true) LS:more (load = false) noLS}. Hierdie skedule is om [Update Time], op [Update Date] op datum gebring."
afr_1_2 = "Wil u dit weer hoor?"
afr_1_2_long = "Indien u hulp van 'n diensagent benodig, kan u enige tyd 'agent' se^. Wil u die skedule vir [suburb] weer hoor? Se^ nou 'ja' of 'nee'"
afr_1_3 = "Wil u oor 'n ander voorstad navraag doen?"
afr_1_3_long = "Indien u hulp van 'n diensagent benodig, kan u enige tyd 'agent' se^. Wil u die skedule vir 'n ander voorstad hoor? Se^ nou 'ja' of 'nee'" 
afr_1_4 = "Dankie dat u die beurtkragdiens van Tshwane Elektrisiteitsdienste geskakel het."

set_0_1 = eng_0_1
set_0_1_long = eng_0_1_long
set_0_2 = ''
set_0_2_long = ''
set_0_3 = ''
set_0_3_long = ''
set_0_4 = ''
set_1_0 = ''
set_1_0_long = ''
set_1_1 = ''
set_1_2 = ''
set_1_2_long = ''
set_1_3 = ''
set_1_3_long = '' 
set_1_4 = ''

