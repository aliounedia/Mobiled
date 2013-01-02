"""
Keeps track of individual call history.

This class should be instantiated at the beginning of a call and
then called throughout the call to add call-flow information.
"""

class CallHistory:
    """ CallHistory class """
    def __init__(self, session_id=None, answer_time=None, caller_number=None,
                 dailed_number=None):
        assert(session_id is not None)
        self.session_id = session_id
        self.answer_time = answer_time
        self.caller_number = caller_number
        self.dailed_number = dailed_number
        self.clear_node_attributes()
        self.nodes = []

    def clear_node_attributes(self):
        """
        Clear node information in preparation for a new node.
        """
        # '_node' attributes refer to the node currently being processed
        self._node_name             = None
        self._node_start_time       = None
        self._node_dtmf             = None
        self._node_dtmf_time        = None
        self._node_dtmf_is_bargin   = None
        self._node_asr_utt          = None
        self._node_asr_score        = None
        self._node_asr_level        = None
        self._node_asr_is_bargin    = None
        self._node_asr_bargin_time  = None
        self._node_record_silence_percentage = None
        self._node_hash_terminated = None
        self._node_is_timeout       = None
        self._node_is_invalid       = None
        self._node_is_maxtries      = None
        self._custom                = None

    def set_hangup_time(self, hangup_time):
        """
        Set call hangup time.
        @param hangup_time: time of hangup
        @type hangup_time: C{datetime}
        """
        self.hangup_time = hangup_time

    def start_node(self, name, start_time):
        """
        Set new node start information.
        @param name: node name
        @type name: C{str}
        @param start_time: node start time
        @type start_time: C{datetime}
        """
        self._node_name        = name
        self._node_start_time  = start_time

    def set_asr_results(self, utt, score, level, is_bargin, bargin_time):
        """
        Set ASR results for the current node.
        @param utt: utterance
        @type utt: C{str}
        @param score: score
        @type score: C{str}
        @param level: level
        @type level: C{int}
        @param is_bargin: signify bargin
        @type is_bargin: C{bool}
        @param bargin_time: time of bargin
        @type bargin_time: C{datetime}
        """
        self._node_asr_utt          = utt
        self._node_asr_score        = score
        self._node_asr_level        = level
        self._node_asr_is_bargin    = is_bargin
        self._node_asr_bargin_time  = bargin_time

    def set_dtmf_results(self, dtmf, dtmf_time, is_bargin):
        """
        Set DTMF results for the current node.
        @param dtmf: DTMF input
        @type dtmf: C{str}
        @param dtmf_time: DTMF input time
        @type dtmf_time: C{datetime}
        @param is_bargin: True if barge-in was detected, otherwise False
        @type is_bargin: C{bool}
        """
        self._node_dtmf            = dtmf
        self._node_dtmf_time       = dtmf_time
        self._node_dtmf_is_bargin  = is_bargin

    def set_is_timeout(self, is_timeout):
        """
        Signifies whether timeout occurred in the current node.
        @param is_timeout: True signifies a timeout, otherwise False
        @type is_timeout: C{bool}
        """
        self._node_is_timeout = is_timeout

    def set_record_results(self, silence_percentage, hash_terminated):
        """
        Sets the record results for the current node
        @param silence_percentage: percentage silence in the recording
        @type silence_percentage: C{str}
        @param hash_terminated: if the call was hash terminated
        @type hash_terminated: C{str}
        """
        self._node_record_silence_percentage = silence_percentage
        self._node_hash_terminated = hash_terminated
        
    def set_is_invalid(self, is_invalid):
        """
        Signifies whether invalid input occurred in the current node.
        @param is_invalid: True signifies invalid input, otherwise False
        @type is_invalid: C{bool}
        """
        self._node_is_invalid = is_invalid

    def set_is_maxtries(self, is_maxtries):
        """
        Signifies whether the max tries was reached for the current node.
        @param is_maxtries: signify maxtries
        @type is_maxtries: C{bool}
        """
        self._node_is_maxtries = is_maxtries

    def set_custom(self, custom):
        """
        Set custom history information.
        @param custom: custom history
        @type custom: C{dic}
        """
        self._custom = custom

    def end_node(self, end_time):
        """
        Close out the current node and append it to the node history.
        @param end_time: end time of the node
        @type end_time: C{datetime}
        """
        self.nodes.append( { 'name':             self._node_name,
                             'start_time':       self._node_start_time,
                             'end_time':         end_time,
                             'dtmf':             self._node_dtmf,
                             'dtmf_time':        self._node_dtmf_time,
                             'dtmf_is_bargin':   self._node_dtmf_is_bargin,
                             'asr_utterance':    self._node_asr_utt,
                             'asr_score':        self._node_asr_score,
                             'asr_level':        self._node_asr_level,
                             'asr_is_bargin':    self._node_asr_is_bargin,
                             'asr_bargin_time':  self._node_asr_bargin_time,
                             'record_silence_percentage':self._node_record_silence_percentage,
                             'record_hash_terminated':self._node_hash_terminated,
                             'is_timeout':       self._node_is_timeout,
                             'is_invalid':       self._node_is_invalid,
                             'is_maxtries':      self._node_is_maxtries,
                             'custom':           self._custom } )
        self.clear_node_attributes()

    def dictify(self):
        """
        Convert the given node into a dictionary in preparation for
        committing to a database.
        @returns: dictionary representation of call history.
        @rtype: C{dict}
        """
        return {
            'session_id':       self.session_id,
            'caller_number':    self.caller_number,
            'dailed_number':    self.dailed_number,
            'answer_time':      self.answer_time,
            'hangup_time':      self.hangup_time,
            'nodes':            self.nodes
        }

    def __str__(self):
        rep = 'session_id::        %s' %self.session_id
        return rep
