# -*- coding: utf-8 -*-
#    Tichy
#
#    copyright 2008 Guillaume Chereau (charlie@openmoko.org)
#
#    This file is part of Tichy.
#
#    Tichy is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Tichy is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Tichy.  If not, see <http://www.gnu.org/licenses/>.

"""
The tasklet module is a very powerfull tool that allow us to write
functions that look like thread (with blocking call), but are in fact
using callback.
"""

__docformat__ = "restructuredtext en"

import sys
from types import GeneratorType

import logging
logger = logging.getLogger('tasklet')


def tasklet(func):
    """Decorator that turns a generator function into a tasklet instance
    """

    def ret(*args, **kargs):
        return Tasklet(generator=func(*args, **kargs))

    ret.__dict__ = func.__dict__
    ret.__name__ = func.__name__
    ret.__doc__ = func.__doc__
    return ret


class Tasklet(object):
    """This class can be used to write easy callback style functions using
    the 'yield' python expression.

    It is usefull in some cases where callback functions are the right
    thing to do, but make the code too messy

    This class is largely inspired by python PEP 0342:
    http://www.python.org/dev/peps/pep-0342/

    See the examples below to understand how to use it.
    """

    def __init__(self, *args, **kargs):
        """Create a new tasklet

        :Keywords:

            generator
                The generator that will be used as a task to run.  If
                this is not defined we use the `run` method of the
                tasklet.
        """
        self.generator = kargs.get('generator', None) or \
            self.do_run(*args, **kargs)
        assert isinstance(self.generator,
                          GeneratorType), type(self.generator)
        # The tasklet we are waiting for...
        self.waiting = None
        self.closed = False

    def do_run(self, *args, **kargs):
        return self.run(*args, **kargs)

    def run(self):
        """The default task run by the tasklet"""
        yield

    def start(self, callback=None, err_callback=None, *args, **kargs):
        """Start the tasklet, connected to a callback and an error callback

        Every additional argument and keyword arguments will be passed
        top the callback method.

        :Parameters:

            callback
                a function that will be called with the returned value
                as argument

            err_callback
                a function that is called if the tasklet raises an
                exception.  The function take 3 arguments as
                parameters, that are the standard python exception
                arguments
        """
        self.callback = callback or self.default_callback
        self.err_callback = err_callback or self.default_err_callback
        self.args = args    # possible additional args that will be
                            # passed to the callback
        self.kargs = kargs  # possible additional keywords args that
                            # will be passed to the callback
        self.send(None)     # And now we can initiate the task

    def default_callback(self, value):
        """The default callback if None is specified"""
        pass

    def default_err_callback(self, type, value, traceback):
        """The default error call back if None is specified"""
        if type is GeneratorExit:
            return
        import traceback as tb
        logger.error("Got error from unconnected tasklet : %s", value)
        lines = tb.format_tb(traceback)
        lines = '\n'.join(lines).split('\n')
        for line in lines:
            logger.error(line)

    def close(self):
        if self.closed:
            return
        if self.waiting:
            self.waiting.close()
        self.generator.close()
        self.closed = True

    def exit(self):
        # TODO: is this really useful, or should we use close here ?
        e = GeneratorExit()
        self.err_callback(type(e), e, sys.exc_info()[2])

    def send(self, value=None, *args):
        """Resume and send a value into the tasklet generator
        """
        # This somehow complicated try switch is used to handle all
        # possible return and exception from the generator function
        assert self.closed == False, "Trying to send to a closed tasklet"
        try:
            value = self.generator.send(value)
        except StopIteration, e:
            # We don't propagate StopIteration
            self.close()
            value = None
        except Exception, e:
            # Make sure we free the memory
            self.close()
            self.err_callback(*sys.exc_info())
            return
        self.handle_yielded_value(value)

    def throw(self, type, value, traceback=None):
        """Throw an exeption into the tasklet generator"""
        try:
            value = self.generator.throw(type, value, traceback)
        except StopIteration, e:
            logger.exception("throw: %s", e)
            # We don't propagate StopIteration
            self.close()
            value = None
        except Exception, e:
            logger.exception("throw: %s", e)
            self.err_callback(*sys.exc_info())
            # Make sure we free the memory
            self.close()
            return
        self.handle_yielded_value(value)

    def handle_yielded_value(self, value):
        """This method is called after the waiting tasklet yielded a value

           We have to take care of two cases:

           - If the value is a Tasklet : we start it and connect the
             call back to the 'parent' Tasklet send and throw hooks

           - Otherwise, we consider that the tasklet finished, and we
             can call our callback function
        """
        if isinstance(value, GeneratorType):
            value = Tasklet(generator=value)
        if isinstance(value, Tasklet):
            self.waiting = value
            value.start(self.send, self.throw)
        else:
            self.callback(value, *self.args, **self.kargs)


class Wait(Tasklet):
    """
    A special tasklet that wait for an event to be emitted

    If o is an Object that can emit a signal 'signal', then we can
    create a tasklet that waits for this event like this : Wait(o,
    'signal')
    """

    def __init__(self, obj, event):
        assert obj is not None
        super(Wait, self).__init__()
        self.obj = obj
        self.event = event
        self.connect_id = None
        #logger.info("%s waiting for '%s'", str(self.obj), str(self.event))

    def _callback(self, o, *args):
        """This is the callback that is triggered by the signal"""
        assert o is self.obj

        if not self.connect_id:
            return # We have been closed already We need to remember
                   # to disconnect to the signal
        o.disconnect(self.connect_id)
        self.connect_id = None

        #logger.info("on %s called '%s'", str(o), str(self.event))

        # We can finally call our real callback
        try:
            self.callback(*args)
        except Exception, e:
            logger.exception("_callback: %s", e)
            self.err_callback(*sys.exc_info())

        # We give a hint to the garbage collector
        self.obj = self.callback = None
        return False

    def start(self, callback, err_callback, *args):
        assert hasattr(self.obj, 'connect'), self.obj
        self.callback = callback
        self.err_callback = err_callback
        self.connect_id = self.obj.connect(self.event, self._callback, *args)

    def close(self):
        # It is very important to disconnect the callback here !
        if self.connect_id:
            self.obj.disconnect(self.connect_id)
        self.obj = self.callback = self.connect_id = None


class WaitFirst(Tasklet):
    """Waits for the first to return of a list of tasklets.
    """

    def __init__(self, *tasklets):
        super(WaitFirst, self).__init__()
        self.done = None
        self.tasklets = tasklets

    def _callback(self, *args):
        #logger.info("waitfirst returned with %s", str(args))
        i = args[-1]
        values = args[:-1]
        if self.done:
            return
        self.done = True
        self.callback((i, values))
        for t in self.tasklets:
            t.close()
        self.callback = None
        self.tasklets = None

    def start(self, callback=None, err_callback=None):
        self.callback = callback
        self.err_callback = Tasklet.default_err_callback

        # We connect all the tasklets
        for (i, t) in enumerate(self.tasklets):
            t.start(self._callback, err_callback, i)


class WaitDBus(Tasklet):
    """Special tasket that wait for a DBus call"""

    def __init__(self, method, *args):
        super(WaitDBus, self).__init__()
        self.method = method
        self.args = args

    def start(self, callback, err_callback):
        self.callback = callback
        self.err_callback = err_callback
        kargs = {'reply_handler': self._callback,
                 'error_handler': self._err_callback}
        logger.debug("call dbus method %s", self.method)
        self.method(*self.args, **kargs)

    def _callback(self, *args):
        logger.debug("got reply from dbus method %s", self.method)
        # Trick to avoid returning a tuple when the method only retrn
        # one value
        if len(args) == 1:
            args = args[0]
        self.callback(args)

    def _err_callback(self, e):
        logger.debug("got error reply from dbus method %s", self.method)
        self.err_callback(type(e), e, sys.exc_info()[2])

# TODO: move all the tichy/dbus related tasklets into
#       paroli-service/phone because that is the only place where it
#       is used

class WaitDBusSignal(Tasklet):
    """A special tasklet that waits for a DBUs event to be emited"""
    def __init__(self, obj, event, time_out = None):
        super(WaitDBusSignal, self).__init__()
        self.obj = obj
        self.event = event
        self.time_out = time_out
        self.connection = None
        self.timeout_connection = None

    def _callback(self, *args):
        if not self.connection:
            return # We have been closed already
        self.connection.remove()
        # don't forget to remove the timeout callback
        if self.timeout_connection:
            import tichy
            tichy.mainloop.source_remove(self.timeout_connection)
            self.timeout_connection = None

        if len(args) == 1:  # What is going on here is that if we have a single value, we return it directly,
            args = args[0]  # but if we have several value we pack them in a tuple for the callback
                            # because the callback only accpet a single argument

        try:
            self.callback(args, *self.args)
        except:
            import sys
            self.err_callback(*sys.exc_info())

        self.obj = self.callback = None
        return False

    def _err_callback(self):
        # can only be called on timeout
        self.timout_connection = None
        e = Exception("TimeOut")
        self.err_callback(type(e), e, sys.exc_info()[2])

    def start(self, callback, err_callback, *args):
        import tichy
        self.callback = callback
        self.err_callback = err_callback
        self.args = args
        self.connection = self.obj.connect_to_signal(self.event, self._callback)
        if self.time_out:
            self.timeout_connection = tichy.mainloop.timeout_add(self.time_out * 1000, self._err_callback)

    def close(self):
        # Note : it is not working very well !!!! Why ? I don't know...
        if self.connection:
            self.connection.remove()
        if self.timeout_connection:
            import tichy
            tichy.mainloop.source_remove(self.timeout_connection)
        self.obj = self.callback = self.connection = self.timeout_connection = None



class Sleep(Tasklet):
    """Tasklet that will return after a given number of seconds"""
    def __init__(self, t):
        """
        init the tasklet

        :Parameter:
            t : int | None
                The time we wait in seconds. If set to None, wait
                forever.
        """

        super(Sleep, self).__init__()
        self.t = t
        self.connection = None

    def _callback(self):
        self.connection = None
        self.callback(*self.args, **self.kargs)

    def start(self, callback, err_callback, *args, **kargs):
        import tichy

        if self.t is None:      # None make us wait infinitively
            return

        self.callback = callback
        self.args = args
        self.kargs = kargs
        self.connection = tichy.mainloop.timeout_add(
            self.t * 1000, self._callback)

    def close(self):
        if self.connection:
            import tichy
            tichy.mainloop.source_remove(self.connection)


class Producer(Tasklet):
    """A Producer is a modified Tasklet that is not automatically closed
    after returing a value.

    This is still expermimental...
    """

    def send(self, value=None, *args):
        """Resume and send a value into the tasklet generator"""
        # This somehow complicated try switch is used to handle all
        # possible return and exception from the generator function
        try:
            value = self.generator.send(value)
        except Exception, e:
            logger.exception("send: %s", e)
            self.close()
            self.err_callback(*sys.exc_info())
            return
        self.handle_yielded_value(value)

    def throw(self, type, value, traceback):
        """Throw an exeption into the tasklet generator"""
        try:
            value = self.generator.throw(type, value, traceback)
        except Exception, e:
            logger.exception("throw: %s", e)
            self.close()
            self.err_callback(*sys.exc_info())
            return
        self.handle_yielded_value(value)


class WaitDBusNameChange(Tasklet):
    """Tasklet that will wait until a dbus name owner change"""
    def run(self, name, time_out=None, session=False):
        import dbus
        import tichy
        if session:
            bus = dbus.SessionBus(mainloop=tichy.mainloop.dbus_loop)
        else:
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        bus_obj = bus.get_object('org.freedesktop.DBus',
                                              '/org/freedesktop/DBus')
        bus_obj_iface = dbus.proxies.Interface(bus_obj,
                                               'org.freedesktop.DBus')
        while True:
            var = yield WaitDBusSignal(bus_obj_iface, 'NameOwnerChanged',
                                       time_out=time_out)
            if var[0] == name:
                yield None

class WaitDBusName(Tasklet):
    """tasklet that waits until a dbus name is present

    If the name is already present, returns immediately.
    """
    def _is_dbus_name_present(self, name, session):
        import dbus
        import tichy
        """Check that a dbus name is present"""
        if session:
            bus = dbus.SessionBus(mainloop=tichy.mainloop.dbus_loop)
        else:
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        bus_obj = bus.get_object('org.freedesktop.DBus',
                                 '/org/freedesktop/DBus')
        bus_obj_iface = dbus.proxies.Interface(bus_obj,
                                               'org.freedesktop.DBus')
        all_bus_names = bus_obj_iface.ListNames()
        return name in all_bus_names

    def run(self, name, time_out=None, session=False):
        if self._is_dbus_name_present(name, session):
            #logger.info("%s is present", str(name))
            yield None
        else:
            yield WaitDBusNameChange(name, time_out=time_out, session=session)


if __name__ == '__main__':
    # And here is a simple example application using our tasklet class

    import gobject

    class WaitSomething(Tasklet):
        """This is a 'primitive' tasklet that will trigger our call back after
        a short time
        """

        def __init__(self, time):
            """This tasklet has one parameter"""
            self.time = time

        def start(self, callback, err_callback, *args):
            self.event_id = gobject.timeout_add(self.time,
                                                callback, None, *args)

        def close(self):
            # We cancel the event
            gobject.source_remove(self.event_id)

    def example1():
        print "== Simple example that waits two times for an input event =="
        loop = gobject.MainLoop()

        def task1(x):
            """An example Tasklet generator function"""
            print "task1 started with value %s" % x
            yield WaitSomething(1000)
            print "tick"
            yield WaitSomething(1000)
            print "task1 stopped"
            loop.quit()
        Tasklet(generator=task1(10)).start()
        print 'I do other things'
        loop.run()

    def example2():
        print "== We can call a tasklet form an other tasklet =="

        def task1():
            print "task1 started"
            value = (yield Tasklet(generator=task2(10)))
            print "rask2 returned value %s" % value
            print "task1 stopped"

        def task2(x):
            print "task2 started"
            print "task2 returns"
            yield 2 * x     # Return value
        Tasklet(generator=task1()).start()

    def example3():
        print "== We can pass exception through tasklets =="

        def task1():
            try:
                yield Tasklet(generator=task2())
            except TypeError:
                print "task2 raised a TypeError"
                yield Tasklet(generator=task4())

        def task2():
            try:
                yield Tasklet(generator=task3())
            except TypeError:
                print "task3 raised a TypeError"
                raise

        def task3():
            raise TypeError
            yield 10

        def task4():
            print 'task4'
            yield 10

        Tasklet(generator=task1()).start()

    def example4():
        print "== We can cancel execution of a task before it ends =="
        loop = gobject.MainLoop()

        def task():
            print "task started"
            yield WaitSomething(1000)
            print "task stopped"
            loop.quit()

        task = Tasklet(generator=task())
        task.start()
        # At this point, we decide to cancel the task
        task.close()
        print "task canceled"

    def example5():
        print "== A task can choose to perform specific action" \
            "if it is canceled =="
        loop = gobject.MainLoop()

        def task():
            print "task started"
            try:
                yield WaitSomething(1000)
            except GeneratorExit:
                print "Executed before the task is canceled"
                raise
            print "task stopped"
            loop.quit()

        task = Tasklet(generator=task())
        task.start()
        # At this point, we decide to cancel the task
        task.close()
        print "task canceled"

    def example6():
        print "== Using WaitFirst, we can wait for several tasks"\
            "at the same time =="
        loop = gobject.MainLoop()

        def task1(x):
            print "Wait for the first task to return"
            value = yield WaitFirst(WaitSomething(2000), WaitSomething(1000))
            print value
            loop.quit()

        Tasklet(generator=task1(10)).start()
        loop.run()

    def example7():
        print "== Using Producer, we can create pipes =="

        class MyProducer(Producer):

            def run(self):
                for i in range(3):
                    yield WaitSomething(1000)
                    yield i

        class MyConsumer(Tasklet):

            def run(self, input):
                print "start"
                try:
                    while True:
                        value = yield input
                        print "get value %s" % value
                except StopIteration:
                    print "Stop"
                loop.quit()

        loop = gobject.MainLoop()
        MyConsumer(MyProducer()).start()
        print "We can do other things in the meanwhile"

        loop.run()

    def test():
        print "== Checking memory usage =="

        def task1():
            yield None

        import gc

        gc.collect()
        n = len(gc.get_objects())

        for i in range(1000):
            t = Tasklet(generator=task1())
            t.start()
            del t

        gc.collect()
        print len(gc.get_objects()) - n

#    test()
#    example1()
#    example2()
#    example3()
#    example4()
#    example6()
    example7()
