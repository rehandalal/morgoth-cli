import base64
import configparser
import gnupg

from morgoth import CONFIG_PATH


class GPGImproperlyConfigured(Exception):
    pass


class Settings(object):
    _path = None

    def __init__(self, path):
        self.config = configparser.ConfigParser()
        self.path = path

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value != self._path:
            self._path = value
            with open(self._path, 'a+') as f:
                f.seek(0)
                self.config.read_file(f)

    @property
    def gpg(self):
        if not self.get('gpg.fingerprint'):
            raise GPGImproperlyConfigured()

        return gnupg.GPG(binary=self.get('gpg.binary'), homedir=self.get('gpg.homedir'),
                         use_agent=True)



    @staticmethod
    def _parse_key(key):
        keys = key.split('.', 1)
        if len(keys) < 2:
            keys = ['morgoth'] + keys
        return keys

    def _encrypt(self, value):
        encrypted = self.gpg.encrypt(value, self.get('gpg.fingerprint'))
        return base64.b64encode(str(encrypted).encode()).decode()

    def _decrypt(self, value):
        decoded = base64.b64decode(value.encode()).decode()
        return self.gpg.decrypt(decoded)

    def get(self, key, default=None, decrypt=False):
        keys = self._parse_key(key)

        try:
            value = self.config[keys[0]][keys[1]]
        except KeyError:
            return default

        if decrypt:
            return self._decrypt(value)
        return value

    def _set(self, key, value):
        keys = self._parse_key(key)

        if not keys[0] in self.config:
            self.config[keys[0]] = {}

        self.config[keys[0]][keys[1]] = value

    def set(self, key, value):
        keys = self._parse_key(key)

        if keys == ['morgoth', 'password']:
            value = self._encrypt(value)

        self._set(key, value)

    def delete(self, key):
        keys = self._parse_key(key)
        del self.config[keys[0]][keys[1]]

    def save(self):
        with open(self.path, 'w') as f:
            self.config.write(f)


settings = Settings(CONFIG_PATH)
