@set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
def _state_change_handler(self, ev):
    datapath=ev.datapath
    if(ev.state==MAIN_DISPATCHER):
	if(self.datapaths[datapath.id].datapath == None):
	    self.logger.info('register datapath:%016x', datapath.id)
	    self.datapaths[datapath.id].datapath=datapath
	elif(ev.state==DEAD_DISPATCHER):
	    if(datapath.id in self.datapaths):
		self.logger.info('unregister datapath:%016x',datapath.id)
		del self.datapaths[datapath.id]
