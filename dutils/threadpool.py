# obtained from http://code.activestate.com/recipes/203871/ MIT
import threading
from time import sleep
import sys

# Ensure booleans exist (not needed for Python 2.2.1 or higher)
try:
    True
except NameError:
    False = 0
    True = not False

class ThreadPool:

    """Flexible thread pool class.  Creates a pool of threads, then
    accepts tasks that will be dispatched to the next available
    thread."""
    
    def __init__(self, numThreads):

        """Initialize the thread pool with numThreads workers."""
        
        self.__threads = []
        self.__resizeLock = threading.Condition(threading.Lock())
        self.__taskLock = threading.Condition(threading.Lock())
        self.__tasks = []
        self.__isJoining = False
        self.__errorHandler = None
        self.setThreadCount(numThreads)

    def setErrorHandler(self, errorHandler):
        self.__errorHandler = errorHandler

    def getErrorHandler(self) :
        return self.__errorHandler

    def setThreadCount(self, newNumThreads):

        """ External method to set the current pool size.  Acquires
        the resizing lock, then calls the internal version to do real
        work."""
        
        # Can't change the thread count if we're shutting down the pool!
        if self.__isJoining:
            return False
        
        self.__resizeLock.acquire()
        try:
            self.__setThreadCountNolock(newNumThreads)
        finally:
            self.__resizeLock.release()
        return True

    def __setThreadCountNolock(self, newNumThreads):
        
        """Set the current pool size, spawning or terminating threads
        if necessary.  Internal use only; assumes the resizing lock is
        held."""
        
        # If we need to grow the pool, do so
        while newNumThreads > len(self.__threads):
            newThread = ThreadPoolThread(self)
            self.__threads.append(newThread)
            newThread.start()
        # If we need to shrink the pool, do so
        while newNumThreads < len(self.__threads):
            self.__threads[0].goAway()
            del self.__threads[0]

    def getThreadCount(self):

        """Return the number of threads in the pool."""
        
        self.__resizeLock.acquire()
        try:
            return len(self.__threads)
        finally:
            self.__resizeLock.release()

    def queueTask(self, task, args=None, taskCallback=None):

        """Insert a task into the queue.  task must be callable;
        args and taskCallback can be None."""
        
        if self.__isJoining == True:
            return False
        if not callable(task):
            return False
        
        self.__taskLock.acquire()
        try:
            self.__tasks.append((task, args, taskCallback))
            return True
        finally:
            self.__taskLock.release()

    def getNextTask(self):

        """ Retrieve the next task from the task queue.  For use
        only by ThreadPoolThread objects contained in the pool."""
        
        self.__taskLock.acquire()
        try:
            if self.__tasks == []:
                return (None, None, None)
            else:
                return self.__tasks.pop(0)
        finally:
            self.__taskLock.release()
    
    def joinAll(self, waitForTasks = True, waitForThreads = True, timeout = None):

        """ Clear the task queue and terminate all pooled threads,
        optionally allowing the tasks and threads to finish."""
        
        # Mark the pool as joining to prevent any more task queueing
        self.__isJoining = True

        # Wait for tasks to finish
        if waitForTasks:
            while self.__tasks != []:
                sleep(.1)

        # Tell all the threads to quit
        self.__resizeLock.acquire()
        try:
            self.__setThreadCountNolock(0)
            self.__isJoining = True

            # Wait until all threads have exited
            if waitForThreads:
                for t in self.__threads:
                    t.join(timeout)
                    del t

            # Reset the pool for potential reuse
            self.__isJoining = False
        finally:
            self.__resizeLock.release()


        
class ThreadPoolThread(threading.Thread):

    """ Pooled thread class. """
    
    threadSleepTime = 0.1

    def __init__(self, pool):

        """ Initialize the thread and remember the pool. """
        
        threading.Thread.__init__(self)
        self.__pool = pool
        self.__isDying = False
        
    def run(self):

        """ Until told to quit, retrieve the next task and execute
        it, calling the callback if any.  """
        
        while self.__isDying == False:
            cmd, args, callback = self.__pool.getNextTask()
            # If there's nothing to do, just sleep a bit
            try:
                if cmd is None:
                    sleep(ThreadPoolThread.threadSleepTime)
                elif callback is None:
                    cmd(args)
                else:
                    callback(cmd(args))
            except:
                if self.__pool.getErrorHandler() :
                    self.__pool.getErrorHandler()(args, sys.exc_info())
                else :
                    print "Unexpected error:", sys.exc_info()
    
    def goAway(self):

        """ Exit the run loop next time through."""
        
        self.__isDying = True

# Usage example
if __name__ == "__main__":

    from random import randrange

    # Sample task 1: given a start and end value, shuffle integers,
    # then sort them
    
    def sortTask(data):
        print "SortTask starting for ", data
        numbers = range(data[0], data[1])
        for a in numbers:
            rnd = randrange(0, len(numbers) - 1)
            a, numbers[rnd] = numbers[rnd], a
        print "SortTask sorting for ", data
        numbers.sort()
        print "SortTask done for ", data
        return "Sorter ", data

    # Sample task 2: just sleep for a number of seconds.

    def waitTask(data):
        print "WaitTask starting for ", data
        print "WaitTask sleeping for %d seconds" % data
        sleep(data)
        if data == 5:
          raise ValueError()
        return "Waiter", data

    # Both tasks use the same callback

    def taskCallback(data):
        print "Callback called for", data

    # Create a pool with three worker threads

    pool = ThreadPool(3)

    # Insert tasks into the queue and let them run
    pool.queueTask(sortTask, (1000, 100000), taskCallback)
    pool.queueTask(waitTask, 5, taskCallback)
    pool.queueTask(sortTask, (200, 200000), taskCallback)
    pool.queueTask(waitTask, 2, taskCallback)
    pool.queueTask(sortTask, (3, 30000), taskCallback)
    pool.queueTask(waitTask, 7, taskCallback)

    # When all tasks are finished, allow the threads to terminate
    pool.joinAll()
