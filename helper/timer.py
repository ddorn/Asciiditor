from _thread import start_new_thread
from time import sleep


def repeat_every(seconds, start_offset=0, ignore_exceptions=False):
    """
    Repeat a function with a given number of seconds between them.

    You can use func.stop = Falseto stop it
    And func.interval to change the interval
    if ignore_exceptions is True, then the thread will continue to call the func even if there is an exception.
    Otherwise it will stop.
    """

    def decorator_every_something(f):

        # they should be accessible from outside so the user can stop it
        f.stop = False
        f.interval = seconds
        f.ignore_exceptions = ignore_exceptions

        def repeater():
            sleep(start_offset)
            while not f.stop:
                try:
                    f()
                except Exception:
                    if not f.ignore_exceptions:
                        raise

                sleep(f.interval)
        start_new_thread(repeater, ())

        return f

    return decorator_every_something

