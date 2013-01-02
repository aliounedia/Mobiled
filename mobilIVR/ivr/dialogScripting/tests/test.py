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

from dialog import Dialog, DialogError

import sys
import re
import traceback


def duck(text, valid, to):
    
    print text
    if to != 0:
        answer = None
        while not answer:
            print "Enter your choice:"
            answer = sys.stdin.readline()
                    
        return answer.strip('\n')
    else:
        return 0


d = Dialog()
d.setGlobals('0_1_system_intro')
d.addNode('0_1_system_intro', 4000, 
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_init'},
                  1:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_0_1'}},
          error={'UNKNOWN':'0_2_wrong_input', 
                 'TIMEOUT':'0_3_no_input'}, 
          options={'english':'1_0_suburb_prompt', 
                   'afrikaans':'1_0_suburb_prompt',
                   'setswana':'1_0_suburb_prompt'})




d.addNode('1_0_suburb_prompt', 4000,
          error={'UNKNOWN':'0_2_wrong_input', 
                 'TIMEOUT':'0_3_no_input'}, 
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_1_0'}},
          options={'lynnwood':'1_1_loadshedding', 
                   'brooklyn':'1_1_loadshedding'}) 
          #TODO: need to add all suburbs

d.addNode('1_1_loadshedding', 0, 
          error={'UNKNOWN':'0_2_wrong_input', 
                 'TIMEOUT':'0_3_no_input'}, 
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_1_1'}},
          goto='EVAL: if (last==1_2_repeat:1_3_another_suburb) else (1_2_repeat)')

d.addNode('1_2_repeat', 4000, 
          error={'UNKNOWN':'0_2_wrong_input', 
                 'TIMEOUT':'0_3_no_input'}, 
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_1_2'}},
          options={'yes':'1_1_loadshedding', 
                   'no':'1_3_another_suburb'})

d.addNode('1_3_another_suburb', 4000, 
          error={'UNKNOWN':'0_2_wrong_input', 
                 'TIMEOUT':'0_3_no_input'}, 
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_1_3'}},
          options={'yes':'1_0_suburb_prompt', 
                   'no':'1_4_exit'})

d.addNode('1_4_exit', 0, exit=True,
          error={'UNKNOWN':'IGNORE', 'TIMEOUT':'IGNORE'}, 
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_1_4'}})
                         
d.addNode('0_2_wrong_input', 0, goto='PREVIOUS',
          error={'UNKNOWN':'IGNORE', 'TIMEOUT':'IGNORE'},
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_wrong_input'}})
                           
d.addNode('0_3_no_input', 0, goto='PREVIOUS',
          error={'UNKNOWN':'IGNORE', 'TIMEOUT':'IGNORE'},
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_no_input'}})

d.addNode('0_4_operator', 0, exit=True,
          error={'UNKNOWN':'IGNORE', 'TIMEOUT':'IGNORE'}, 
          custom={0:{'PATH':None, 'MODULE':'test_custom', 
                     'CLASS':None, 'FUNCTION':'custom_0_4'}})

try:
    d.run(duck, duck, duck, duck, '')
    d.writeStats('stats.log')
    #print
except DialogError, e:
    traceback.print_exc()
            
    print e
        