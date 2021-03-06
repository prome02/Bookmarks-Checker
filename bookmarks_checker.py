#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Bookmarks Checker """


import argparse
import os
import re
import threading
import time
import urllib.request


class BookmarksChecker(object):

    """
        Bookmarks Checker
        Verify links in a Chrome or Firefox exported bookmarks file.

        Usage              python bookmarks_checker.py [-f file]

        Python Version     3.x
        Author             Martin Latter
        Copyright          Martin Latter 21/09/2017
        Version            0.05
        Credits            Doug Hellmann (threading usage)
        License            GNU GPL version 3.0 (GPL v3); http://www.gnu.org/licenses/gpl.html
        Link               https://github.com/Tinram/Bookmarks-Checker.git
    """


    DEBUG = False
    USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'
    NUMBER_THREADS = 16

    num_urls = 0
    dead_link_counter = 0
    url_parse_time = 0
    parse_flag = False
    url_index = {}


    def __init__(self):

        """ Initialise and execute methods. """

        filename = self.get_args()
        self.check_file(filename)
        self.parse_file(filename)


    def get_args(self):

        """ Parse the command line arguments. """

        parser = argparse.ArgumentParser()

        parser.add_argument(
            '-f', '--file',
            dest='filename',
            help='Specify filename of the bookmarks file to load',
            default='bookmarks.html',
            type=str,
            action='store')

        args = parser.parse_args()

        return args.filename


    def check_file(self, filename):

        """
            Check bookmark file existence and access.
            Args:
                filename: name of bookmarks file.
        """

        if not os.access(filename, os.R_OK):
            print('\n %s cannot be found or cannot be read.\n' % filename)
            os._exit(-1)


    def parse_file(self, filename):

        """
            Parse the file, extract links, and set-up threads.
            Args:
                filename: name of bookmarks file.
        """

        urls = []
        thread_holder = []

        with open(filename) as bmfile:
            for line in bmfile:
                full_url = re.findall(r'(<a\s[^>]*href=\"([^\"]*)\"[^>]*>(.*)<\/a>)', line, re.I)
                if full_url:
                    urls.append(full_url[0][1])
                    self.url_index[full_url[0][1]] = full_url[0][2]

        if not len(urls):
            print('\n No links extracted from %s\n' % filename)
            os._exit(-1)

        pool = ActivePool()
        semaphore = threading.Semaphore(self.NUMBER_THREADS)

        self.url_parse_time = time.time()

        for url in urls:

            current_url = url

            thread = threading.Thread(
                target=self.activate_thread,
                name=current_url,
                args=(semaphore, pool, current_url)
            )

            thread_holder.append(thread)

        self.num_urls = len(urls)

        print('\n %i links being checked ...' % self.num_urls)

        if not self.DEBUG:
            print('\n failures:\n')

        for thrd in thread_holder:
            thrd.start()

        for thrd in thread_holder:
            thrd.join()

        self.display_final_info()


    def activate_thread(self, semaphore, pool, url):

        """
            Activate thread to check a URL.
            Args:
                semaphore: threading semaphore.
                pool: instance of ActivePool()
                url: a single URL.
        """

        with semaphore:
            name = threading.current_thread().getName()
            pool.activate(name)
            self.check_url(url)
            pool.deactivate(name)


    def check_url(self, url):

        """
            Thread method to check URL access.
            Args:
                url: a single URL.
        """

        headers = {'User-Agent': self.USER_AGENT}

        try:
            url_name = self.url_index[url]
            req = urllib.request.Request(url, None, headers)
            response = urllib.request.urlopen(req)
            # print(response.getcode())
            if self.DEBUG:
                print(' ok: %s  |  %s' % (url_name, url))

        except urllib.error.HTTPError as err2:
            self.dead_link_counter += 1
            if not self.DEBUG:
                print(' F:  %s  |  %s -- %s' % (url_name, url, str(err2.code)))

        except urllib.error.URLError as err1:
            self.dead_link_counter += 1
            if not self.DEBUG:
                print('\t %s  |  %s' % (url_name, url))
            else:
                print(' F:  %s  |  %s -- %s' % (url_name, url, str(err1.reason)))

        except:
            pass


    def display_final_info(self):

        """ Display dead link count and URL parse time. """

        print('\n %i links failed' % self.dead_link_counter)
        print(' %i links verified\n' % (self.num_urls - self.dead_link_counter))
        print(' URL parse time: %s secs\n' % str.format('{0:.5f}', (time.time() - self.url_parse_time)))

# end class


class ActivePool(object):

    """
        Active pool of threads.

        Python Version     3.x
        Author             Doug Hellmann
    """

    def __init__(self):
        super(ActivePool, self).__init__()
        self.active = []
        self.lock = threading.Lock()

    def activate(self, name):

        """ Activate thread. """

        with self.lock:
            self.active.append(name)

    def deactivate(self, name):

        """ Deactivate thread. """

        with self.lock:
            self.active.remove(name)

# end class



def main():

    """ Invoke class. """

    BookmarksChecker()


if __name__ == '__main__':

    main()
