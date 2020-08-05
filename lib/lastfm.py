import requests
import string
import os
import json
import time
import random

class API:
    def __init__(self,
            key, url='http://ws.audioscrobbler.com/2.0/',
            verbose=True, cache='lastfm.dat', cache_age=86400,
            use_api_for_top=True, top_albums_file='top_albums.txt'):
        
        self.key = key
        self.url = url
        self.verbose = verbose

        self.use_api_for_top = use_api_for_top
        self.top_albums_file = top_albums_file

        self._default_cache = {'top': {'created': time.time(), 'data': []}, 'searches': {}}

        self.cache_path = cache
        self.cache_age = cache_age
        if not os.path.exists(os.path.dirname(self.cache_path)):
            self._log('Cache directory does not exist, creating')
            os.mkdir(os.path.dirname(self.cache_path))
        if not os.path.exists(self.cache_path):
            self._log('Cache file does not exist, creating')
            self.cache = self._default_cache
            self._save_cache()
        else:
            with open(self.cache_path, 'r') as f:
                try:
                    self.cache = json.load(f)
                    self._log('Cache file loaded from \'%s\'' % self.cache_path)
                except json.decoder.JSONDecodeError:
                    self.cache = self._default_cache
                    self._log('Cache file corrupted, resetting file')
                    self._save_cache()
        
        self._sweep_search_cache()
    
    def _sweep_search_cache(self, save_cache=True):
        to_delete = []
        for query in self.cache['searches']:
            if self._update_search_cache(query):
                to_delete.append(query)
        
        for query in to_delete:
            del self.cache['searches'][query]
        if len(to_delete): self._log('Deleted %s expired searches from search cache' % len(to_delete))
        else: self._log('No expired searches found in cache. Nothing deleted')
        if len(to_delete) and save_cache: self._save_cache()
    
    def _uniform_query(self, query):
        query = query.lower()
        query = query.translate(str.maketrans('', '', string.punctuation.replace('.', '')))
        query = sorted(query.split())
        return ' '.join(query)

    def _log(self, *args, **kwargs):
        if self.verbose:
            print('[LastFM]', *args, **kwargs)

    def _save_cache(self):
        with open(self.cache_path, 'w+') as f:
            json.dump(self.cache, f)
    
    def _update_search_cache(self, query):
        if query not in self.cache['searches']: return True
        if time.time() - self.cache['searches'][query]['created'] > self.cache_age: return True
        return False

    def _update_top_cache(self):
        if not len(self.cache['top']['data']): return True
        if time.time() - self.cache['top']['created'] > self.cache_age: return True
        return False

    def _request(self, **kwargs):
        url = self.url + '?format=json&api_key=%s' % self.key
        for arg in kwargs:
            url += '&%s=%s' % (arg, kwargs[arg])

        resp = requests.get(url)
        return resp.json()

    def search(self, query, use_cache=True, save_cache=True):
        query = self._uniform_query(query)
        if not use_cache or self._update_search_cache(query):
            self._log('Searching for \'%s\'' % query)
            resp = self._request(method='album.search', album=query)
            try: results = resp['results']['albummatches']['album']
            except KeyError: results = []

            albums = []
            for album in results:
                images = album['image']

                if images[0]['#text']:
                    albums.append({
                        'name': album['name'],
                        'artist': album['artist'],
                        'image_large': images[3]['#text'],
                        'image': images[2]['#text'],
                        'image_small': images[1]['#text'],
                        'image_tiny': images[0]['#text']
                    })
            
            self.cache['searches'][query] = {'created': time.time(), 'data': albums}
            if save_cache: self._save_cache()

        albums = self.cache['searches'][query]['data']
        return albums

    def top(self, use_cache=True, save_cache=True):
        if self.use_api_for_top:
            if not use_cache or self._update_top_cache():
                self._log('Fetching top albums from LastFM')
                resp = self._request(method='chart.gettoptracks')
                results = resp['tracks']['track']

                top = []
                for i, track in enumerate(results):
                    search = self.search(track['name'] + ' ' + track['artist']['name'], save_cache=False)
                    if len(search):
                        album = search[0]
                        self._log('(%s/%s) Fetched %s - %s' % (i+1, len(results), album['name'], album['artist']))
                        top.append(search[0])
                random.shuffle(top)
                self.cache['top'] = {'created': time.time(), 'data': top}
                if save_cache: self._save_cache()
        else:
            with open(self.top_albums_file, 'r') as f:
                self._log('Fetching top albums from \'%s\'' % self.top_albums_file)
                results = f.read().split('\n\n')

                top = []
                for i, lines in enumerate(results):
                    album, artist = lines.split('\n')
                    search = self.search(album + ' ' + artist, save_cache=False)
                    if len(search):
                        album = search[0]
                        self._log('(%s/%s) Fetched %s - %s' % (i+1, len(results), album['name'], album['artist']))
                        top.append(search[0])
                # random.shuffle(top)
                self.cache['top'] = {'created': time.time(), 'data': top}
                if save_cache: self._save_cache()

        return self.cache['top']['data']