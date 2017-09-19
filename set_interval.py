from threading import Timer


class Interval:
    def __init__(self, func, secs):
        # Fuction to be called back
        self.func = func
        # Interval
        self.secs = secs
        # Called back after calling self.func
        self.refresh_cb = None
        # if 0, it won't join
        self.join_timeout = 0
        # Start right away
        self._refresh_interval()

    def _refresh_interval(self):
        # Call function
        self.func()
        # Refresh timer object
        self.timer = Timer(self.secs, self._refresh_interval)
        self.timer.start()
        # Call control function if set
        if self.refresh_cb is not None:
            self.refresh_cb(self)
        # Join thread if specified
        if self.join_timeout != 0:
            self.join(self.join_timeout)

    def set(self, secs):
        '''
        Override set secs on Interval construction
        '''
        self.secs = secs
        # Cancel previous timer and run new one
        self.cancel()
        self._refresh_interval()

    def cancel(self):
        # Cancel interval
        self.timer.cancel()

    def join(self, timeout=None):
        # Join interval
        self.join_timeout = timeout
        self.timer.join(timeout)

    def on_refresh(self, callback):
        # Set control function
        self.refresh_cb = callback


if __name__ == '__main__':
    def test_func():
        print('test_func')

    class TestClass:
        def __call__(self):
            print('TestClass')

    interval = Interval(TestClass(), 1)

    def stop_after_six(i):
        if not hasattr(i, 'sas_count'):
            i.sas_count = 1

        if i.sas_count == 5:
            i.cancel()

        i.sas_count += 1

    interval.on_refresh(stop_after_six)
    interval.join()
