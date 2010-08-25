#!/usr/bin/env python
"""
_WorkSpecParser_

A class that parses WMSpec files and provides relevant info
"""

__all__ = []
__revision__ = "$Id: WorkSpecParser.py,v 1.14 2009/09/24 20:16:22 sryu Exp $"
__version__ = "$Revision: 1.14 $"

from urllib import urlopen
from WMCore.Services.DBS.DBSReader import DBSReader
from WMCore.WMSpec.WMWorkload import getWorkloadFromTask
#TODO: Pull useful stuff out of wmspec then free it - large data structure
#TODO: Cleanup, logArchive etc. WorkflowTypes needed???

#globalDBS = 'http://cmsdbsprod.cern.ch/cms_dbs_prod_global/servlet/DBSServlet'

class WorkSpecParser:
    """
    Helper object to parse a WMSpec and return chunks of work
    """

    def __init__(self, task):
        self.wmspec = getWorkloadFromTask(task)
        self.initialTask = task
        self.splitAlgo = self.initialTask.jobSplittingAlgorithm()
        self.splitSize = self.initialTask.jobSplittingParameters()["size"]

#TODO: Resume this kind of thing at some point
#    def parse(self):
#        """Parse spec file & cache useful info"""
#        import pickle
#        input = open(self.specUrl)
#        spec = pickle.load(input) #TODO: Replace by WMSpec load method
#        initialTask = spec.taskIterator().next()
#        
#        self.validateWorkflow(spec, initialTask)
#        
#        # get useful stuff
#        params = self.specParams
#        params['whitelist'] = getattr(initialTask,
#                                      'constraints.sites.whitelist', ())
#        params['blacklist'] = getattr(initialTask,
#                                      'constraints.sites.blacklist', ())
#        params['priority'] = getattr(spec.data, 'Priority', 1)
#        params['dbs'] = getattr(spec.data, 'dbs', globalDBS)
#        params['input_datasets'] = getattr(initialTask.data.parameters,
#                                           'inputDatasets', ())
#        del initialTask, spec
#        input.close()


    def split(self, split = True, dbs_pool = None):
        """
        Take the wmspec and divide into units of work
        
        A unit of work corresponds to a significant 
          amount i.e. processing a block
        
        defaultBlockSize is used for WMSpecs that don't contain 
        splitting criteria i.e. Generation jobs
        """
        #self.validateWorkflow()
        results = []
        inputDataset = self.initialTask.inputDataset()
        if not inputDataset:
            # we don't have any input data - divide into one chunk
            jobs = self.__estimateJobs(self.splitSize, 
                                       self.initialTask.totalEvents())
            results.append((None, [], jobs))
            return results

        # data processing - need to contact dbs
        dbsUrl = self.initialTask.dbsUrl()
        if dbs_pool and dbs_pool.has_key(dbsUrl):
            dbs = dbs_pool[dbsUrl]
        else:
            dbs = DBSReader(dbsUrl)

        datasetPath = "/%s/%s/%s" % (inputDataset.primary, 
                                     inputDataset.processed, 
                                     inputDataset.tier)
        # prob don't need to handle multiple input datasets but just in case
        if not split:
            # Don't split
            # ignore parentage as dataset parents not always set
            self.parentFlag = False
            dsInfo = dbs.getDatasetInfo(datasetPath)
            results.append(self._calculateParamsForData(dsInfo))
        else:
            # Split by block. Assume blocks are reasonable size
            for block in dbs.getFileBlocksInfo(datasetPath):
                results.append(self._calculateParamsForData(block))

        return results


    def _calculateParamsForData(self, data):
        """
        Calculate the properties for the data item given
        """
        # block and datasets have different names
        if  self.splitAlgo == 'EventBased':
            jobs = self.__estimateJobs(self.splitSize,
                                       data.get('NumEvents',
                                                data.get('number_of_events')))
        elif self.splitAlgo == 'FileBased':
            jobs = self.__estimateJobs(self.splitSize,
                                       data.get('NumFiles',
                                                data.get('number_of_files')))
        else:
            raise RuntimeError, \
                        'Unsupported Splitting algo: %s' % self.splitAlgo

        parents = []
        if self.initialTask.parentProcessingFlag():
            parents = data['Parents']
            if not parents:
                msg = "Parentage required but no parents found for %s"
                raise RuntimeError, msg % data['Name']

        return (data.get('Name', data.get('path')), parents, jobs)

#    #Was used to split production into multiple blocks
#    #Now dont split these
#    def __split_no_input(self):
#        """
#        We have no input data - split by events
#        """
#        results = []
#        total = getattr(self.initialTask, 'totalEvents', 10000)
#        perJob = getattr(self.initialTask, 'splitSize', 10)
#        blockTotal = self.defaultBlockSize * perJob
#        count = 0
#        while total > 0:
#            jobs = self.__estimateJobs(perJob, blockTotal)
#            count += 1
#            total -= (jobs * perJob)
#            results.append(WorkUnit(str(count), None, (), jobs))
#            if total < blockTotal: blockTotal = total
#        return results


    def __estimateJobs(self, unit, total):
        """
        Estimate the number of jobs resulting from a block of work
        """
        #TODO: Possibility to run JobSplitting in DryRun mode, need changes
        # there for this though. Also maybe unnecessary as subscriptions need 
        # a fileset setup etc... might be able to fake without
        # persisting in db... for now fake this
        count = 0
        while total > 0:
            count += 1
            total -= unit
        return count


#TODO: validation code needs to move to WMWorkloadHelper
#    def validateWorkflow(self):
#        """Check necessary params set"""
#        required = ('splitType', 'splitSize')
#        for key in required:
#            try:
#                getattr(self, key)
#            except AttributeError:
#                msg = "Required parameter \'%s\' missing from %s"
#                raise RuntimeError, msg % (key, self.specUrl)
#        for site in self.whitelist:
#            if site in self.blacklist:
#                msg = "Site \'%s\' in both white & black lists"
#                raise RuntimeError, msg
#        if self.inputDatasets:
#            return self.validateForProcessing()
#        else:
#            return self.validateForProduction()
#
#
#    def validateForProduction(self):
#        """Check for needed production params"""
#        if self.splitType != 'Event':
#            msg = "splitType == %s, only \'Event\' valid for workflows with no input" % self.splitType
#            raise RuntimeError, msg
#        if not self.totalEvents:
#            msg = "Production type workflow missing \'totalEvents\' parameter"
#            raise RuntimeError, msg
#
#
#    def validateForProcessing(self):
#        """Check for needed processing params"""
#        if self.totalEvents:
#            msg = "Processing type workflow cannot have totalEvents parameter"
#            raise RuntimeError, msg


#    def simpleMemoize(self, name, obj, item, default = None):
#        """Poor mans memoize"""
#        try:
#            return self.specParams[name]
#        except IndexError:
#            if default:
#                value = getattr(obj, item, default)
#            else:
#                value = getattr(obj, item)
#            self.specParams[name] = value
#            return value
