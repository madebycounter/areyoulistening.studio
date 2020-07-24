from .helpers import random_string
import requests
import shutil
import os
import json
import time

class ImageCache:
    def __init__(self, data='images.dat', dump='images/', domains=[], verbose=True, cache_age=86400):
        self._data_path = data
        self._dump_path = dump
        self._default_data = {'images': {}}

        self.cache_age = cache_age
        self.verbose = True
        self.domains = domains

        if not os.path.exists(self._dump_path):
            os.makedirs(self._dump_path)
            self._log('Dump directory does not exist, creating')

        if not os.path.exists(self._data_path):
            self._log('Cache file does not exist, creating')
            self.data = self._default_data
            self._save_data()
        else:
            with open(self._data_path, 'r') as f:
                try:
                    self.data = json.load(f)
                    self._log('Data file loaded from \'%s\'' % self._data_path)
                except json.decoder.JSONDecodeError:
                    self._log('Data file corrupted, resetting cache')
                    self.data = self._default_data
                    self.delete_all()
                    self._save_data()

        if not len(self.domains):
            self._log('Warning: cache running without a whitelist')

    def _log(self, *args, **kwargs):
        if self.verbose: print('[ImageCache]', *args, **kwargs)
    
    def _save_data(self):
        with open(self._data_path, 'w+') as f:
            json.dump(self.data, f)
            # self._log('Data file saved')
    
    def _make_valid_path(self):
        path = random_string(8)
        while path in self.data:
            path = random_string(8)
        return path
    
    def sweep_cache(self):
        to_remove = []
        for url in self.data['images']:
            if time.time() - self.data['images'][url]['age'] > self.cache_age:
                to_remove.append(url)

        for url in to_remove:
            del self.data['images'][url]

        files_deleted = 0
        cached_imgs = [ self.data['images'][a]['filename'] for a in self.data['images'] ]
        for img in os.listdir(self._dump_path):
            if img not in cached_imgs:
                os.remove(self._dump_path + img)
                files_deleted += 1
        
        self._log('Removed %s expired images' % len(to_remove))
        self._log('Removed %s images unknown to the cache' % (files_deleted - len(to_remove)))
        self._save_data()

    def delete_all(self):
        shutil.rmtree(self._dump_path)
        os.makedirs(self._dump_path)
        self.data = self._default_data
        self._save_data()
        self._log('All images purged from cache')
    
    def get_image(self, url, save_data=True):
        is_allowed = False
        for domain in self.domains:
            if url.startswith(domain): is_allowed = True
        
        if not is_allowed and len(self.domains):
            raise Exception('domain not whitelisted allowed')

        if url in self.data['images']:
            filename = self.data['images'][url]['filename']
            self.data['images'][url]['age'] = time.time()
        else:
            resp = requests.get(url, stream=True)
            filename = self._make_valid_path() + '.' + url.split('.')[-1]
            self._log('Downloading \'%s\' as %s' % (url, filename))
            with open(self._dump_path + filename, 'wb') as f:
                shutil.copyfileobj(resp.raw, f)
            del resp
            self.data['images'][url] = {
                'filename': filename,
                'age': time.time()
            }
        if save_data: self._save_data()
        return self._dump_path + filename