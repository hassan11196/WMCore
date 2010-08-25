#!/usr/bin/env python
"""
_Save_

MySQL implementation of Jobs.Save
"""

__all__ = []
__revision__ = "$Id: Save.py,v 1.8 2009/09/09 21:22:00 mnorman Exp $"
__version__ = "$Revision: 1.8 $"

from WMCore.Database.DBFormatter import DBFormatter

class Save(DBFormatter):
    sql = """UPDATE wmbs_job SET jobgroup = :jobgroup, name = :name, 
               couch_record = :couch_record, outcome = :outcome, cache_dir = :cache_dir,
               location = 
                 (SELECT id FROM wmbs_location WHERE site_name = :location)
             WHERE id = :jobid"""
    
    def execute(self, jobid, jobgroup, name, couch_record, location, outcome, cache_dir,  
                conn = None, transaction = False):
        if outcome == 'success':
            boolOutcome = 1
        else:
            boolOutcome = 0
        
        binds = {"jobid": jobid, "jobgroup": jobgroup, "name": name, 
                 "couch_record": couch_record, "location": location, 
                 "outcome": boolOutcome, "cache_dir": cache_dir}

        self.dbi.processData(self.sql, binds, conn = conn,
                             transaction = transaction)
        return
